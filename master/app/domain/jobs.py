from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timezone

from shared.models import CrawlJobConfig, CrawlJobOut, JobStatus, SchedulingMode
from shared.urlnorm import domain_of, normalize_url

from ..db.database import Database, dump, iso, load, parse_dt
from . import frontier
from .hub import EventHub

log = logging.getLogger("crawlmesh.jobs")

BENCH_VERSION = "bench-v2"


def _is_bench_seed(url: str) -> bool:
    from shared.netinfo import local_ip

    host = domain_of(url)
    if host in (local_ip(), "127.0.0.1", "localhost"):
        return "/bench" in url
    return False


def workload_key(config: CrawlJobConfig) -> str:
    parts = [
        BENCH_VERSION,
        ",".join(sorted(config.seed_urls)),
        str(config.maximum_pages),
        str(config.maximum_depth),
        str(config.batch_size),
        str(config.request_timeout),
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


async def create_job(
    db: Database,
    hub: EventHub,
    config: CrawlJobConfig,
    *,
    worker_allowlist: list[str] | None = None,
    mode: str = "distributed",
    experiment_id: str | None = None,
) -> CrawlJobOut:
    seeds = [url for url in (normalize_url(u) for u in config.seed_urls) if url]
    if not seeds:
        raise ValueError("Seed URL tidak valid (harus http/https absolut)")

    allowed = [d.lower().strip() for d in config.allowed_domains if d.strip()]
    if not allowed:
        allowed = sorted({domain_of(url) for url in seeds})

    allow_private = config.allow_private_targets or all(_is_bench_seed(url) for url in seeds)
    if not allow_private:
        from shared.urlnorm import is_safe_public_url

        unsafe = [url for url in seeds if not is_safe_public_url(url)]
        if unsafe:
            raise ValueError(
                "Seed URL menuju jaringan privat/loopback. Aktifkan allow_private_targets "
                "hanya untuk target benchmark lokal."
            )

    job_id = f"job-{secrets.token_hex(5)}"
    now = iso()
    key = workload_key(config)

    await db.write(
        """INSERT INTO jobs
           (job_id, job_name, seed_urls, allowed_domains, maximum_pages, maximum_depth,
            batch_size, request_timeout, domain_delay, respect_robots, user_agent,
            scheduling_mode, include_subdomains, allow_private_targets, worker_allowlist,
            status, workload_key, created_at, started_at, mode, experiment_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?)""",
        (
            job_id,
            config.job_name,
            dump(seeds),
            dump(allowed),
            config.maximum_pages,
            config.maximum_depth,
            config.batch_size,
            config.request_timeout,
            config.domain_delay,
            1 if config.respect_robots else 0,
            config.user_agent,
            config.scheduling_mode.value,
            1 if config.include_subdomains else 0,
            1 if allow_private else 0,
            dump(worker_allowlist or []),
            key,
            now,
            now,
            mode,
            experiment_id,
        ),
    )

    job = await db.fetch_one("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    assert job is not None
    await frontier.enqueue_urls(db, job, [(url, 0) for url in seeds])
    await db.write(
        "UPDATE jobs SET status='running' WHERE job_id=?", (job_id,)
    )

    out = await get_job(db, job_id)
    assert out is not None
    await hub.broadcast("job.updated", out.model_dump(mode="json"))
    log.info("job created %s seeds=%d", job_id, len(seeds))
    return out


def _job_out(row: dict, stats: dict | None = None) -> CrawlJobOut:
    stats = stats or {}
    started = parse_dt(row["started_at"])
    completed = parse_dt(row["completed_at"])
    throughput = float(row["throughput"] or 0.0)
    if started and stats.get("pages_crawled"):
        end = completed or datetime.now(timezone.utc)
        elapsed = max((end - started).total_seconds(), 0.001)
        throughput = round(int(stats["pages_crawled"]) / elapsed, 3)

    return CrawlJobOut(
        job_id=row["job_id"],
        job_name=row["job_name"],
        seed_urls=load(row["seed_urls"], []),
        allowed_domains=load(row["allowed_domains"], []),
        maximum_pages=row["maximum_pages"],
        maximum_depth=row["maximum_depth"],
        batch_size=row["batch_size"],
        request_timeout=row["request_timeout"],
        domain_delay=row["domain_delay"],
        respect_robots=bool(row["respect_robots"]),
        scheduling_mode=SchedulingMode(row["scheduling_mode"]),
        status=JobStatus(row["status"]),
        created_at=parse_dt(row["created_at"]) or datetime.now(timezone.utc),
        started_at=started,
        completed_at=completed,
        pages_crawled=int(stats.get("pages_crawled", row["pages_crawled"] or 0)),
        pages_failed=int(stats.get("pages_failed", row["pages_failed"] or 0)),
        pages_pending=int(stats.get("pages_pending", 0)),
        tasks_total=int(stats.get("tasks_total", 0)),
        tasks_completed=int(stats.get("tasks_completed", 0)),
        tasks_failed=int(stats.get("tasks_failed", 0)),
        throughput=throughput,
    )


async def _stats(db: Database, job_id: str) -> dict:
    row = await db.fetch_one(
        """SELECT
             (SELECT COUNT(*) FROM results WHERE job_id = :job AND error IS NULL) AS pages_crawled,
             (SELECT COUNT(*) FROM results WHERE job_id = :job AND error IS NOT NULL) AS pages_failed,
             (SELECT COUNT(*) FROM frontier_urls WHERE job_id = :job AND state IN ('queued','scheduled')) AS pages_pending,
             (SELECT COUNT(*) FROM tasks WHERE job_id = :job) AS tasks_total,
             (SELECT COUNT(*) FROM tasks WHERE job_id = :job AND status = 'completed') AS tasks_completed,
             (SELECT COUNT(*) FROM tasks WHERE job_id = :job AND status IN ('failed','dead')) AS tasks_failed""",
        {"job": job_id},
    )
    return {k: int(v or 0) for k, v in (row or {}).items()}


async def get_job(db: Database, job_id: str) -> CrawlJobOut | None:
    row = await db.fetch_one("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    if row is None:
        return None
    return _job_out(row, await _stats(db, job_id))


async def list_jobs(db: Database, limit: int = 50, include_experiments: bool = False) -> list[CrawlJobOut]:
    where = "" if include_experiments else "WHERE experiment_id IS NULL"
    rows = await db.fetch_all(
        f"SELECT * FROM jobs {where} ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    jobs = []
    for row in rows:
        jobs.append(_job_out(row, await _stats(db, row["job_id"])))
    return jobs


async def set_status(
    db: Database, hub: EventHub, job_id: str, status: JobStatus
) -> CrawlJobOut | None:
    row = await db.fetch_one("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    if row is None:
        return None
    current = JobStatus(row["status"])

    if status == JobStatus.PAUSED and current != JobStatus.RUNNING:
        return _job_out(row, await _stats(db, job_id))
    if status == JobStatus.RUNNING and current not in (JobStatus.PAUSED, JobStatus.PENDING):
        return _job_out(row, await _stats(db, job_id))
    if status == JobStatus.CANCELLED and current in (JobStatus.COMPLETED, JobStatus.CANCELLED):
        return _job_out(row, await _stats(db, job_id))

    if status == JobStatus.COMPLETED:
        await db.write(
            "UPDATE jobs SET status=?, completed_at=? WHERE job_id=?",
            (status.value, iso(), job_id),
        )
    elif status == JobStatus.CANCELLED:
        await db.write(
            "UPDATE jobs SET status=?, completed_at=? WHERE job_id=?",
            (status.value, iso(), job_id),
        )
    else:
        await db.write("UPDATE jobs SET status=? WHERE job_id=?", (status.value, job_id))

    if status == JobStatus.CANCELLED:
        await db.write(
            "UPDATE tasks SET status='cancelled' WHERE job_id=? AND status IN ('queued','leased','running')",
            (job_id,),
        )
        await db.write(
            "UPDATE frontier_urls SET state='cancelled' WHERE job_id=? AND state IN ('queued','scheduled')",
            (job_id,),
        )

    out = await get_job(db, job_id)
    if out:
        await hub.broadcast("job.updated", out.model_dump(mode="json"))
    return out


async def complete_if_done(db: Database, hub: EventHub, job_id: str) -> bool:
    row = await db.fetch_one("SELECT status, maximum_pages FROM jobs WHERE job_id = ?", (job_id,))
    if row is None or row["status"] != JobStatus.RUNNING.value:
        return False
    pending_frontier = await db.scalar(
        "SELECT COUNT(*) FROM frontier_urls WHERE job_id=? AND state IN ('queued','scheduled')",
        (job_id,),
    )
    pending_tasks = await db.scalar(
        "SELECT COUNT(*) FROM tasks WHERE job_id=? AND status IN ('queued','leased','running')",
        (job_id,),
    )
    if int(pending_frontier) or int(pending_tasks):
        return False
    await db.write(
        "UPDATE jobs SET status='completed', completed_at=? WHERE job_id=?",
        (iso(), job_id),
    )
    out = await get_job(db, job_id)
    if out:
        await hub.broadcast("job.completed", out.model_dump(mode="json"))
    log.info("job completed %s", job_id)
    return True


async def start_job(db: Database, hub: EventHub, job_id: str) -> CrawlJobOut | None:
    return await set_status(db, hub, job_id, JobStatus.RUNNING)
