from __future__ import annotations

import asyncio
import json
import logging
import secrets
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from multiprocessing import get_context

import psutil

from shared.models import (
    CrawlJobConfig,
    CrawlResultItem,
    JobStatus,
    SchedulingMode,
    TaskResultRequest,
)
from shared.netinfo import local_ip

from ..db.database import Database, dump, iso, load, parse_dt
from . import aggregator, jobs, scheduler
from .hub import EventHub

log = logging.getLogger("crawlmesh.experiments")

SCALABILITY_STEPS = [1, 2, 4, 6, 9]
RUNNING: dict[str, asyncio.Task] = {}
SPECS: dict[str, "RunSpec"] = {}
CANCELLED: set[str] = set()


@dataclass
class RunSpec:
    experiment_type: str
    worker_count: int = 0
    seed_urls: list[str] = field(default_factory=lambda: [f"http://{local_ip()}:8000/bench/"])
    maximum_pages: int = 60
    maximum_depth: int = 1
    batch_size: int = 5
    request_timeout: float = 10.0
    domain_delay: float = 0.02
    scheduling_mode: str = "dynamic"
    repeat: int = 3

    def to_config(self) -> dict:
        return {
            "seed_urls": self.seed_urls,
            "maximum_pages": self.maximum_pages,
            "maximum_depth": self.maximum_depth,
            "batch_size": self.batch_size,
            "request_timeout": self.request_timeout,
            "domain_delay": self.domain_delay,
            "scheduling_mode": self.scheduling_mode,
            "repeat": self.repeat,
        }

    def job_config(self, worker_count: int) -> CrawlJobConfig:
        label = {
            "sequential": "Sequential baseline",
            "local_parallel": f"Local parallel ×{worker_count}",
            "distributed": f"Distributed ×{worker_count}",
        }.get(self.experiment_type, self.experiment_type)
        return CrawlJobConfig(
            job_name=f"bench:{label}",
            seed_urls=self.seed_urls,
            maximum_pages=self.maximum_pages,
            maximum_depth=self.maximum_depth,
            batch_size=self.batch_size,
            request_timeout=self.request_timeout,
            domain_delay=self.domain_delay,
            scheduling_mode=SchedulingMode(self.scheduling_mode),
            allow_private_targets=True,
        )


class ExperimentBusy(RuntimeError):
    pass


def is_running() -> bool:
    return any(not task.done() for task in RUNNING.values())


async def _insert_experiment(
    db: Database,
    spec: RunSpec,
    *,
    experiment_type: str,
    worker_count: int,
    group_id: str | None = None,
    status: str = "pending",
) -> str:
    exp_id = f"exp-{secrets.token_hex(5)}"
    config = spec.job_config(max(1, worker_count))
    key = jobs.workload_key(config)
    await db.write(
        """INSERT INTO experiments
           (experiment_id, experiment_type, worker_count, workload_key, scheduling_mode,
            status, group_id, total_pages, config, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            exp_id,
            experiment_type,
            worker_count,
            key,
            spec.scheduling_mode,
            status,
            group_id or exp_id,
            spec.maximum_pages,
            dump(spec.to_config()),
            iso(),
        ),
    )
    return exp_id


async def _set_status(
    db: Database,
    hub: EventHub,
    exp_id: str,
    status: str,
    error: str | None = None,
    notes: str | None = None,
) -> dict | None:
    fields = ["status = ?"]
    params: list = [status]
    if status in ("completed", "failed", "cancelled"):
        fields.append("finished_at = ?")
        params.append(iso())
    if error is not None:
        fields.append("error = ?")
        params.append(error)
    if notes is not None:
        fields.append("notes = ?")
        params.append(notes)
    params.append(exp_id)
    await db.write(f"UPDATE experiments SET {', '.join(fields)} WHERE experiment_id = ?", params)
    row = await get_experiment(db, exp_id)
    if row:
        await hub.broadcast("experiment.updated", row)
    return row


async def start(db: Database, hub: EventHub, spec: RunSpec) -> dict:
    if is_running():
        raise ExperimentBusy("Eksperimen lain sedang berjalan")
    exp_type = spec.experiment_type
    exp_id = await _insert_experiment(
        db,
        spec,
        experiment_type=exp_type,
        worker_count=spec.worker_count or (4 if exp_type == "local_parallel" else 1),
    )
    SPECS[exp_id] = spec
    RUNNING[exp_id] = asyncio.create_task(_execute(db, hub, exp_id))
    RUNNING[exp_id].add_done_callback(lambda _task: RUNNING.pop(exp_id, None))
    row = await get_experiment(db, exp_id)
    return row or {}


async def _execute(db: Database, hub: EventHub, exp_id: str) -> None:
    spec = SPECS.get(exp_id)
    started = time.perf_counter()
    try:
        if spec is None:
            raise RuntimeError("Spesifikasi eksperimen hilang")
        await _set_status(db, hub, exp_id, "running")
        if spec.experiment_type == "scalability":
            await _run_scalability(db, hub, exp_id, spec, started)
        else:
            await _run_single(db, hub, exp_id, spec, spec.worker_count, started)
        await _set_status(db, hub, exp_id, "completed")
        log.info("experiment completed %s", exp_id)
    except asyncio.CancelledError:
        await _set_status(db, hub, exp_id, "cancelled")
        raise
    except Exception as exc:  # noqa: BLE001
        log.exception("experiment failed %s", exp_id)
        await _set_status(db, hub, exp_id, "failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        SPECS.pop(exp_id, None)
        CANCELLED.discard(exp_id)


async def cancel(db: Database, hub: EventHub, exp_id: str) -> dict | None:
    CANCELLED.add(exp_id)
    task = RUNNING.get(exp_id)
    if task is not None and not task.done():
        task.cancel()
    jobs_rows = await db.fetch_all(
        """SELECT job_id FROM jobs WHERE status IN ('running','paused') AND experiment_id IN (
             SELECT experiment_id FROM experiments WHERE experiment_id=? OR group_id=?
           )""",
        (exp_id, exp_id),
    )
    for row in jobs_rows:
        await jobs.set_status(db, hub, row["job_id"], JobStatus.CANCELLED)
    await db.write(
        "UPDATE tasks SET status='cancelled' WHERE job_id IN (SELECT job_id FROM jobs WHERE experiment_id=?) AND status IN ('queued','leased','running')",
        (exp_id,),
    )
    return await _set_status(db, hub, exp_id, "cancelled")


# --------------------------------------------------------------------------
# Single experiment
# --------------------------------------------------------------------------


async def _run_single(
    db: Database,
    hub: EventHub,
    exp_id: str,
    spec: RunSpec,
    worker_count: int,
    started: float,
    group_id: str | None = None,
) -> None:
    exp_type = spec.experiment_type
    worker_count = max(1, worker_count)
    baseline = await _baseline(db, spec)
    await _warm_bench(spec.seed_urls[0])

    runs = [await _attempt(db, hub, exp_id, spec, worker_count) for _ in range(max(1, spec.repeat))]
    runs.sort(key=lambda run: run["exec_ms"])
    chosen = runs[len(runs) // 2]
    exec_ms = chosen["exec_ms"]
    pages_ok = max(run["pages_ok"] for run in runs)
    pages_failed = max(run["pages_failed"] for run in runs)
    cpu_avg = sum(run["cpu"] for run in runs) / len(runs)
    mem_avg = sum(run["mem"] for run in runs) / len(runs)
    samples = chosen["samples"]
    if pages_ok == 0:
        raise RuntimeError(
            "Eksperimen tidak menghasilkan halaman (job selesai sebelum worker memproses)"
        )
    throughput = pages_ok / max(exec_ms / 1000, 0.001)
    speedup = None
    efficiency = None
    if exp_type == "sequential":
        speedup = 1.0
        efficiency = 100.0
    elif baseline and baseline["execution_time_ms"]:
        speedup = round(baseline["execution_time_ms"] / max(exec_ms, 1), 3)
        efficiency = round((speedup / worker_count) * 100, 2)

    await _persist_samples(db, exp_id, samples)
    await db.write(
        """UPDATE experiments SET
             execution_time_ms=?, pages_ok=?, pages_failed=?, speedup=?, efficiency=?,
             throughput=?, cpu_utilization=?, memory_utilization=?, baseline_id=?,
             progress_pages=?, worker_count=?, status='completed', finished_at=?
           WHERE experiment_id=?""",
        (
            round(exec_ms, 2),
            pages_ok,
            pages_failed,
            speedup,
            efficiency,
            round(throughput, 3),
            round(cpu_avg, 2),
            round(mem_avg, 2),
            baseline["experiment_id"] if baseline else None,
            pages_ok,
            worker_count,
            iso(),
            exp_id,
        ),
    )
    row = await get_experiment(db, exp_id)
    if row:
        await hub.broadcast("experiment.updated", row)


async def _attempt(
    db: Database, hub: EventHub, exp_id: str, spec: RunSpec, worker_count: int
) -> dict:
    """One measured run of the workload, returns raw metrics."""
    exp_type = spec.experiment_type

    if exp_type == "distributed":
        workers = await _active_worker_ids(db)
        if not workers:
            raise RuntimeError("Tidak ada worker aktif untuk eksperimen distributed")
        chosen = workers[:worker_count]
        if len(chosen) < worker_count:
            raise RuntimeError(f"Butuh {worker_count} worker aktif, tersedia {len(chosen)}")
        job = await jobs.create_job(
            db,
            hub,
            spec.job_config(worker_count),
            worker_allowlist=chosen,
            mode="distributed",
            experiment_id=exp_id,
        )
        run_started = time.perf_counter()
        sampler = asyncio.create_task(
            _sample(db, hub, exp_id, job.job_id, "distributed", chosen, run_started)
        )
        try:
            await _wait_job(db, hub, exp_id, job.job_id, run_started, spec)
        finally:
            samples = await sampler
        pages_ok, pages_failed = await _job_pages(db, job.job_id)
        exec_ms = (time.perf_counter() - run_started) * 1000
    else:
        workers_n = 1 if exp_type == "sequential" else worker_count
        job = await jobs.create_job(
            db,
            hub,
            spec.job_config(workers_n),
            mode="sequential" if exp_type == "sequential" else "local_parallel",
            experiment_id=exp_id,
        )
        sampler = asyncio.create_task(
            _sample(db, hub, exp_id, job.job_id, "local", [], time.perf_counter())
        )
        try:
            exec_ms = await _run_local(db, hub, exp_id, spec, job.job_id, workers_n)
        finally:
            samples = await sampler
        pages_ok, pages_failed = await _job_pages(db, job.job_id)

    cpu, mem = _averages(samples)
    return {
        "exec_ms": exec_ms,
        "pages_ok": pages_ok,
        "pages_failed": pages_failed,
        "cpu": cpu,
        "mem": mem,
        "samples": samples,
    }


async def _run_scalability(
    db: Database, hub: EventHub, exp_id: str, spec: RunSpec, started: float
) -> None:
    available = await _active_worker_ids(db)
    if not available:
        raise RuntimeError("Tidak ada worker aktif untuk uji scalability")

    await db.write(
        "UPDATE experiments SET worker_count=?, total_pages=? WHERE experiment_id=?",
        (len(available), spec.maximum_pages, exp_id),
    )

    children: list[str] = []
    baseline = await _baseline(db, spec)
    if baseline is None:
        child = await _insert_experiment(
            db, spec, experiment_type="sequential", worker_count=1, group_id=exp_id
        )
        children.append(child)
        await _set_status(db, hub, child, "running")
        seq_spec = replace(spec, experiment_type="sequential")
        await _run_single(db, hub, child, seq_spec, 1, time.perf_counter(), group_id=exp_id)

    for n in SCALABILITY_STEPS:
        if exp_id in CANCELLED:
            raise asyncio.CancelledError()
        if n > len(available):
            continue
        child = await _insert_experiment(
            db, spec, experiment_type="distributed", worker_count=n, group_id=exp_id
        )
        children.append(child)
        await _set_status(db, hub, child, "running")
        dist_spec = replace(spec, experiment_type="distributed")
        await _run_single(db, hub, child, dist_spec, n, time.perf_counter(), group_id=exp_id)

    elapsed = (time.perf_counter() - started) * 1000
    await db.write(
        "UPDATE experiments SET execution_time_ms=?, notes=? WHERE experiment_id=?",
        (round(elapsed, 2), dump({"children": children}), exp_id),
    )
    await _set_status(db, hub, exp_id, "completed")


# --------------------------------------------------------------------------
# Local execution (sequential / local parallel)
# --------------------------------------------------------------------------


async def _run_local(
    db: Database,
    hub: EventHub,
    exp_id: str,
    spec: RunSpec,
    job_id: str,
    workers_n: int,
) -> float:
    from worker.crawler import CrawlFetcher
    from worker.parser_pool import parse_document

    sequential = spec.experiment_type == "sequential"
    label = "local-sequential" if sequential else f"local-parallel-{workers_n}"
    concurrency = 1 if sequential else max(2, workers_n * 2)
    fetcher = CrawlFetcher(user_agent="CrawlMesh-Bench/0.1", concurrency=concurrency)
    pool: ProcessPoolExecutor | None = None
    if not sequential:
        pool = ProcessPoolExecutor(
            max_workers=workers_n, mp_context=get_context("spawn")
        )

    semaphore = asyncio.Semaphore(concurrency)

    # Warm up connections and process pool so measurement reflects crawl work,
    # not one-time interpreter spawn cost.
    warm_payload = {
        "url": "http://warmup.local/",
        "final_url": "http://warmup.local/",
        "html": "<title>warm</title><p>warm</p>",
        "max_links": 1,
    }
    if pool is not None:
        loop = asyncio.get_running_loop()
        future = pool.submit(parse_document, warm_payload)
        await loop.run_in_executor(None, future.result)
    else:
        parse_document(warm_payload)
    seed = spec.seed_urls[0]
    with_origin = seed.split("/")
    warm_url = f"{with_origin[0]}//{with_origin[2]}/robots.txt" if len(with_origin) > 2 else seed
    try:
        await fetcher.fetch(
            warm_url, timeout=10.0, respect_robots=False, domain_delay=0.0, allow_private=True
        )
    except Exception:  # noqa: BLE001 - warm-up is best effort
        pass

    started = time.perf_counter()
    timeout = max(180.0, spec.maximum_pages * 3.0)

    try:
        while True:
            if exp_id in CANCELLED:
                raise asyncio.CancelledError()
            if time.perf_counter() - started > timeout:
                await jobs.set_status(db, hub, job_id, JobStatus.CANCELLED)
                raise TimeoutError("Batas waktu eksperimen terlampaui")

            job = await db.fetch_one("SELECT * FROM jobs WHERE job_id=?", (job_id,))
            if job is None or job["status"] != JobStatus.RUNNING.value:
                break

            await scheduler.decompose_job(db, hub, job, [])
            claimed = await _claim_local(db, job_id, label, 1 if sequential else workers_n)
            if not claimed:
                await jobs.complete_if_done(db, hub, job_id)
                await asyncio.sleep(0.05)
                continue

            if sequential:
                for task in claimed:
                    await _execute_local_task(
                        db, hub, task, fetcher, None, parse_document, semaphore
                    )
            else:
                await asyncio.gather(
                    *(
                        _execute_local_task(
                            db, hub, task, fetcher, pool, parse_document, semaphore
                        )
                        for task in claimed
                    )
                )
    finally:
        await fetcher.close()
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)
    return (time.perf_counter() - started) * 1000


async def _claim_local(
    db: Database, job_id: str, label: str, limit: int
) -> list[dict]:
    rows = await db.fetch_all(
        "SELECT * FROM tasks WHERE job_id=? AND status='queued' ORDER BY task_id LIMIT ?",
        (job_id, limit),
    )
    claimed: list[dict] = []
    from datetime import timedelta

    deadline = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()
    for row in rows:
        await db.write(
            """UPDATE tasks SET status='leased', assigned_worker=?, attempt_count=attempt_count+1,
                   leased_at=?, lease_deadline=? WHERE task_id=?""",
            (label, iso(), deadline, row["task_id"]),
        )
        claimed.append(row)
    return claimed


async def _execute_local_task(
    db: Database,
    hub: EventHub,
    task: dict,
    fetcher,
    pool: ProcessPoolExecutor | None,
    parse_document,
    semaphore: asyncio.Semaphore,
) -> None:
    job = await db.fetch_one("SELECT * FROM jobs WHERE job_id=?", (task["job_id"],))
    if job is None:
        return
    urls = json.loads(task["urls"])
    results: list[CrawlResultItem] = []
    started = time.perf_counter()

    async def fetch_one(url: str) -> dict:
        async with semaphore:
            try:
                return await fetcher.fetch(
                    url,
                    timeout=float(job["request_timeout"]),
                    respect_robots=bool(job["respect_robots"]),
                    domain_delay=float(job["domain_delay"]),
                    allow_private=bool(job["allow_private_targets"]),
                )
            except Exception as exc:  # noqa: BLE001
                return {
                    "url": url,
                    "final_url": url,
                    "http_status": 0,
                    "html": "",
                    "size_bytes": 0,
                    "content_type": "",
                    "response_time_ms": 0.0,
                    "error": f"{type(exc).__name__}: {exc}",
                }

    fetched = [await fetch_one(url) for url in urls]
    loop = asyncio.get_running_loop()

    for item in fetched:
        document = None
        if item.get("html"):
            parse_payload = {
                "url": item["url"],
                "final_url": item.get("final_url") or item["url"],
                "html": item["html"],
                "max_links": 50,
            }
            if pool is not None:
                document = await loop.run_in_executor(pool, parse_document, parse_payload)
            else:
                document = parse_document(parse_payload)
        if document is None:
            results.append(
                CrawlResultItem(
                    url=item["url"],
                    final_url=item.get("final_url") or item["url"],
                    http_status=item["http_status"],
                    response_time_ms=item["response_time_ms"],
                    size_bytes=item.get("size_bytes", 0),
                    content_type=item.get("content_type", ""),
                    error=item.get("error") or "no content",
                )
            )
        else:
            results.append(
                CrawlResultItem(
                    url=item["url"],
                    final_url=document["final_url"],
                    http_status=item["http_status"],
                    title=document["title"],
                    extracted_text=document["text"],
                    links=document["links"],
                    content_hash=document["content_hash"],
                    response_time_ms=item["response_time_ms"],
                    size_bytes=item.get("size_bytes", 0),
                    content_type=item.get("content_type", ""),
                    error=item.get("error"),
                )
            )

    await aggregator.ingest_results(
        db,
        hub,
        task["task_id"],
        TaskResultRequest(
            worker_id=task.get("assigned_worker") or "local",
            results=results,
            processing_ms=round((time.perf_counter() - started) * 1000, 2),
        ),
    )


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


async def _wait_job(
    db: Database,
    hub: EventHub,
    exp_id: str,
    job_id: str,
    started: float,
    spec: RunSpec,
) -> None:
    timeout = max(180.0, spec.maximum_pages * 3.0)
    while True:
        if exp_id in CANCELLED:
            raise asyncio.CancelledError()
        if time.perf_counter() - started > timeout:
            await jobs.set_status(db, hub, job_id, JobStatus.CANCELLED)
            raise TimeoutError("Batas waktu eksperimen terlampaui")
        job = await db.fetch_one("SELECT status FROM jobs WHERE job_id=?", (job_id,))
        if job is None or job["status"] in (
            JobStatus.COMPLETED.value,
            JobStatus.CANCELLED.value,
            JobStatus.FAILED.value,
        ):
            return
        await asyncio.sleep(0.5)


async def _sample(
    db: Database,
    hub: EventHub,
    exp_id: str,
    job_id: str,
    mode: str,
    worker_ids: list[str],
    started: float,
) -> list[dict]:
    samples: list[dict] = []
    while True:
        try:
            pages = await db.scalar(
                "SELECT COUNT(*) FROM results WHERE job_id=? AND error IS NULL", (job_id,)
            )
            if mode == "distributed":
                if worker_ids:
                    placeholders = ",".join("?" for _ in worker_ids)
                    row = await db.fetch_one(
                        f"SELECT AVG(cpu_usage) cpu, AVG(memory_usage) mem FROM nodes WHERE worker_id IN ({placeholders})",
                        worker_ids,
                    )
                    cpu = float((row or {}).get("cpu") or 0)
                    mem = float((row or {}).get("mem") or 0)
                else:
                    cpu = mem = 0.0
            else:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory().percent
            sample = {
                "ts_offset_ms": int((time.perf_counter() - started) * 1000),
                "cpu_usage": round(cpu, 2),
                "memory_usage": round(mem, 2),
                "pages_done": int(pages),
            }
            samples.append(sample)
            await db.write(
                """UPDATE experiments SET cpu_utilization=?, memory_utilization=?,
                       progress_pages=? WHERE experiment_id=?""",
                (round(cpu, 2), round(mem, 2), int(pages), exp_id),
            )
            job = await db.fetch_one("SELECT status FROM jobs WHERE job_id=?", (job_id,))
            if job is None or job["status"] != JobStatus.RUNNING.value:
                break
        except asyncio.CancelledError:
            break
        except Exception:  # noqa: BLE001
            log.exception("sampler error")
        await asyncio.sleep(1.0)
    return samples


async def _persist_samples(db: Database, exp_id: str, samples: list[dict]) -> None:
    if not samples:
        return
    await db.write_many(
        """INSERT INTO experiment_samples
           (experiment_id, ts_offset_ms, cpu_usage, memory_usage, pages_done, throughput)
           VALUES (?, ?, ?, ?, ?, 0)""",
        [
            (exp_id, s["ts_offset_ms"], s["cpu_usage"], s["memory_usage"], s["pages_done"])
            for s in samples
        ],
    )


def _averages(samples: list[dict]) -> tuple[float, float]:
    if not samples:
        return 0.0, 0.0
    cpu = sum(s["cpu_usage"] for s in samples) / len(samples)
    mem = sum(s["memory_usage"] for s in samples) / len(samples)
    return cpu, mem


async def _job_pages(db: Database, job_id: str) -> tuple[int, int]:
    row = await db.fetch_one(
        """SELECT
             SUM(CASE WHEN error IS NULL THEN 1 ELSE 0 END) ok,
             SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) failed
           FROM results WHERE job_id=?""",
        (job_id,),
    )
    return int((row or {}).get("ok") or 0), int((row or {}).get("failed") or 0)


async def _warm_bench(seed: str) -> None:
    """Force the bench site to render every page before the timer starts."""
    if "/bench" not in seed:
        return
    import httpx

    base = seed.split("/bench")[0]
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            await client.get(f"{base}/bench/_warm")
    except httpx.HTTPError:
        log.warning("bench warm-up failed")


async def _active_worker_ids(db: Database) -> list[str]:
    rows = await db.fetch_all(
        """SELECT worker_id FROM nodes
           WHERE role='worker' AND status IN ('online','idle','busy') AND simulated_offline=0
           ORDER BY hostname ASC"""
    )
    return [row["worker_id"] for row in rows]


async def _baseline(db: Database, spec: RunSpec) -> dict | None:
    key = jobs.workload_key(spec.job_config(1))
    return await db.fetch_one(
        """SELECT experiment_id, execution_time_ms FROM experiments
           WHERE experiment_type='sequential' AND workload_key=? AND status='completed'
             AND pages_ok > 0
           ORDER BY created_at DESC LIMIT 1""",
        (key,),
    )


# --------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------


def _row_out(row: dict) -> dict:
    return {
        "experiment_id": row["experiment_id"],
        "experiment_type": row["experiment_type"],
        "worker_count": row["worker_count"],
        "workload_key": row["workload_key"],
        "scheduling_mode": row["scheduling_mode"],
        "status": row["status"],
        "group_id": row["group_id"],
        "progress_pages": row["progress_pages"],
        "total_pages": row["total_pages"],
        "execution_time_ms": row["execution_time_ms"],
        "pages_ok": row["pages_ok"],
        "pages_failed": row["pages_failed"],
        "speedup": row["speedup"],
        "efficiency": row["efficiency"],
        "throughput": row["throughput"],
        "cpu_utilization": row["cpu_utilization"],
        "memory_utilization": row["memory_utilization"],
        "recovery_time_ms": row["recovery_time_ms"],
        "baseline_id": row["baseline_id"],
        "config": load(row["config"]),
        "notes": row["notes"],
        "error": row["error"],
        "created_at": row["created_at"],
        "finished_at": row["finished_at"],
    }


async def list_experiments(
    db: Database, limit: int = 100, group_id: str | None = None
) -> list[dict]:
    if group_id:
        rows = await db.fetch_all(
            "SELECT * FROM experiments WHERE group_id=? ORDER BY created_at ASC", (group_id,)
        )
    else:
        rows = await db.fetch_all(
            "SELECT * FROM experiments ORDER BY created_at DESC LIMIT ?", (limit,)
        )
    return [_row_out(row) for row in rows]


async def get_experiment(db: Database, exp_id: str, with_samples: bool = False) -> dict | None:
    row = await db.fetch_one("SELECT * FROM experiments WHERE experiment_id=?", (exp_id,))
    if row is None:
        return None
    out = _row_out(row)
    if with_samples:
        out["samples"] = await db.fetch_all(
            "SELECT ts_offset_ms, cpu_usage, memory_usage, pages_done FROM experiment_samples WHERE experiment_id=? ORDER BY ts_offset_ms",
            (exp_id,),
        )
    return out
