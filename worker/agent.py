from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from multiprocessing import get_context

import httpx
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from shared.models import (
    CrawlResultItem,
    HeartbeatRequest,
    LeaseRequest,
    RegisterRequest,
    TaskFailRequest,
    TaskResultRequest,
    TaskStatus,
)

from .config import AgentConfig
from .crawler import CrawlFetcher
from .discovery import start_listener
from .monitor import ResourceMonitor
from .parser_pool import parse_document

log = logging.getLogger("crawlmesh.agent")

AGENT_VERSION = "0.1.0"


def _configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-7s %(name)s | %(message)s", "%H:%M:%S")
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    logging.getLogger("httpx").setLevel(logging.WARNING)


class WorkerAgent:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.worker_id = config.worker_id()
        self.cluster_id: str | None = None
        self.assigned = False
        self.node_status = "pending"
        self.inflight = 0
        self.active_tasks: dict[str, dict] = {}
        self.monitor = ResourceMonitor(config.resolved_pool_size(), config.resolved_capacity())
        self.hardware = ResourceMonitor.hardware()
        self._stop = asyncio.Event()
        self._client: httpx.AsyncClient | None = None
        self._requests_ok = 0
        self.fetcher: CrawlFetcher | None = None
        self.pool: ProcessPoolExecutor | None = None
        self._fetch_semaphore = asyncio.Semaphore(max(1, config.fetch_concurrency))

    # ------------------------------------------------------------------ info
    def info(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "hostname": self.config.hostname,
            "ip_address": self.config.local_ip(),
            "port": self.config.port,
            "cpu_cores": self.hardware["cpu_cores"],
            "memory_total": self.hardware["memory_total"],
            "os_name": self.hardware["os_name"],
            "python_version": self.hardware["python_version"],
            "agent_version": AGENT_VERSION,
            "pool_size": self.config.resolved_pool_size(),
            "capacity": self.config.resolved_capacity(),
            "cluster_id": self.cluster_id,
            "assigned": self.assigned,
            "status": self.node_status,
        }

    # ------------------------------------------------------------ lifecycle
    async def start(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.config.master_url.rstrip("/"),
            headers={"X-Cluster-Token": self.config.token},
            timeout=30.0,
        )
        self.fetcher = CrawlFetcher(
            user_agent="CrawlMesh/0.1 (+worker-agent)",
            concurrency=self.config.fetch_concurrency,
        )
        self.pool = ProcessPoolExecutor(
            max_workers=self.config.resolved_pool_size(),
            mp_context=get_context("spawn"),
        )
        log.info(
            "agent %s | master=%s | pool=%s capacity=%s",
            self.worker_id,
            self.config.master_url,
            self.config.resolved_pool_size(),
            self.config.resolved_capacity(),
        )
        if not self.config.token:
            log.warning("CRAWLMESH_TOKEN kosong; master akan menolak registrasi")

    async def stop(self) -> None:
        self._stop.set()
        if self.fetcher is not None:
            await self.fetcher.close()
        if self.pool is not None:
            self.pool.shutdown(wait=False, cancel_futures=True)
        if self._client is not None:
            await self._client.aclose()

    async def run_loops(self) -> None:
        await asyncio.gather(
            self._registration_loop(),
            self._heartbeat_loop(),
            self._lease_loop(),
        )

    # --------------------------------------------------------- registration
    async def _register(self) -> bool:
        assert self._client is not None
        payload = RegisterRequest(
            worker_id=self.worker_id,
            hostname=self.config.hostname,
            ip_address=self.config.local_ip(),
            port=self.config.port,
            cpu_cores=int(self.hardware["cpu_cores"]),
            memory_total=int(self.hardware["memory_total"]),
            os_name=str(self.hardware["os_name"]),
            python_version=platform.python_version(),
            agent_version=AGENT_VERSION,
            pool_size=self.config.resolved_pool_size(),
            capacity=self.config.resolved_capacity(),
        )
        try:
            resp = await self._client.post("/api/worker/register", json=payload.model_dump())
        except httpx.HTTPError as exc:
            log.warning("registrasi gagal (%s), coba lagi 5s", exc)
            return False
        if resp.status_code == 401:
            log.error("registrasi ditolak: pairing token tidak valid")
            return False
        if resp.status_code >= 400:
            log.warning("registrasi HTTP %s: %s", resp.status_code, resp.text[:200])
            return False
        data = resp.json()
        self.worker_id = data.get("worker_id", self.worker_id)
        self.cluster_id = data.get("cluster_id")
        self.assigned = data.get("status") not in ("pending", "removed", "offline")
        self.node_status = data.get("status", "pending")
        log.info(
            "terdaftar di cluster %s sebagai %s (status=%s)",
            self.cluster_id,
            self.worker_id,
            self.node_status,
        )
        return True

    async def _registration_loop(self) -> None:
        while not self._stop.is_set():
            if await self._register():
                return
            await asyncio.sleep(5)

    # ------------------------------------------------------------ heartbeat
    async def _heartbeat_once(self) -> float:
        assert self._client is not None
        metrics = self.monitor.sample(inflight=self.inflight, active_tasks=len(self.active_tasks))
        payload = HeartbeatRequest(
            worker_id=self.worker_id,
            metrics=metrics,
            status=self.node_status,
            current_job_ids=sorted({t.get("job_id", "") for t in self.active_tasks.values()}),
        )
        resp = await self._client.post("/api/worker/heartbeat", json=payload.model_dump(mode="json"))
        if resp.status_code == 404:
            self.assigned = False
            self.node_status = "pending"
            return 2.0
        resp.raise_for_status()
        data = resp.json()
        self.assigned = bool(data.get("assigned"))
        self.node_status = data.get("status", self.node_status)
        self._requests_ok += 1
        return float(self.config.heartbeat_interval)

    async def _heartbeat_loop(self) -> None:
        delay = 1.0
        while not self._stop.is_set():
            try:
                delay = await self._heartbeat_once()
            except httpx.HTTPError as exc:
                log.warning("heartbeat gagal: %s", exc)
                delay = 3.0
            except Exception:  # noqa: BLE001
                log.exception("heartbeat loop error")
                delay = 5.0
            await asyncio.sleep(delay)

    # ---------------------------------------------------------------- lease
    async def _lease_loop(self) -> None:
        while not self._stop.is_set():
            await asyncio.sleep(self.config.lease_interval)
            if not self.assigned or self.inflight >= self.config.resolved_capacity():
                continue
            assert self._client is not None
            try:
                resp = await self._client.post(
                    "/api/worker/lease",
                    json=LeaseRequest(
                        worker_id=self.worker_id,
                        free_slots=self.config.resolved_capacity() - self.inflight,
                    ).model_dump(),
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                tasks = data.get("tasks") or []
                if tasks:
                    await self._accept_tasks(tasks)
            except httpx.HTTPError:
                continue

    async def _accept_tasks(self, tasks: list[dict]) -> None:
        for task in tasks:
            self.active_tasks[task["task_id"]] = {**task, "status": TaskStatus.RUNNING.value}
            self.inflight += 1
            log.info(
                "task %s | job %s | %d url | attempt %s",
                task["task_id"],
                task["job_id"],
                len(task.get("urls", [])),
                task.get("attempt", 1),
            )
            asyncio.create_task(self._execute_task(task))

    async def _fetch_one(self, url: str, lease: dict) -> dict:
        assert self.fetcher is not None
        async with self._fetch_semaphore:
            try:
                return await self.fetcher.fetch(
                    url,
                    timeout=float(lease.get("request_timeout") or 15.0),
                    respect_robots=bool(lease.get("respect_robots", True)),
                    domain_delay=float(lease.get("domain_delay") or 0.0),
                    allow_private=bool(lease.get("allow_private_targets", False)),
                )
            except Exception as exc:  # noqa: BLE001 - one URL must not kill the task
                log.exception("fetch failed %s", url)
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

    async def _parse(self, fetched: dict, lease: dict) -> dict:
        assert self.pool is not None
        loop = asyncio.get_running_loop()
        payload = {
            "url": fetched["url"],
            "final_url": fetched.get("final_url") or fetched["url"],
            "html": fetched.get("html", ""),
            "max_links": int(lease.get("max_links_per_page") or 50),
        }
        try:
            return await loop.run_in_executor(self.pool, parse_document, payload)
        except Exception:  # noqa: BLE001
            log.exception("parse failed %s", fetched["url"])
            return {
                "url": fetched["url"],
                "final_url": payload["final_url"],
                "title": "",
                "text": "",
                "links": [],
                "content_hash": "",
            }

    async def _execute_task(self, lease: dict) -> None:
        assert self._client is not None
        task_id = lease["task_id"]
        urls: list[str] = list(lease.get("urls") or [])
        started = time.perf_counter()
        results: list[CrawlResultItem] = []
        try:
            fetched = await asyncio.gather(*(self._fetch_one(url, lease) for url in urls))
            parsed: dict[str, dict] = {}
            to_parse = [item for item in fetched if item.get("html")]
            if to_parse:
                outputs = await asyncio.gather(*(self._parse(item, lease) for item in to_parse))
                parsed = {output["url"]: output for output in outputs}

            for item in fetched:
                document = parsed.get(item["url"])
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
                    self.monitor.note_page(0.0)
                    continue
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
                self.monitor.note_page(item["response_time_ms"])

            payload = TaskResultRequest(
                worker_id=self.worker_id,
                results=results,
                links=[],
                processing_ms=round((time.perf_counter() - started) * 1000, 2),
            )
            response = await self._client.post(
                f"/api/worker/tasks/{task_id}/result", json=payload.model_dump(mode="json")
            )
            if response.status_code >= 400:
                log.warning(
                    "result rejected for %s: HTTP %s %s",
                    task_id,
                    response.status_code,
                    response.text[:200],
                )
                await self._fail_task(task_id, f"result rejected HTTP {response.status_code}")
            else:
                body = response.json()
                log.info(
                    "task %s done | accepted %s dup %s links %s",
                    task_id,
                    body.get("accepted"),
                    body.get("duplicates"),
                    body.get("links_accepted"),
                )
        except Exception as exc:  # noqa: BLE001
            log.exception("task %s crashed", task_id)
            await self._fail_task(task_id, f"{type(exc).__name__}: {exc}")
        finally:
            self.inflight = max(0, self.inflight - 1)
            self.active_tasks.pop(task_id, None)

    async def _fail_task(self, task_id: str, error: str) -> None:
        assert self._client is not None
        with contextlib.suppress(httpx.HTTPError):
            await self._client.post(
                f"/api/worker/tasks/{task_id}/fail",
                json=TaskFailRequest(
                    worker_id=self.worker_id, error=error, retriable=True
                ).model_dump(),
            )


# ---------------------------------------------------------------- HTTP app
def create_app(agent: WorkerAgent) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _configure_logging()
        await agent.start()
        transport, _ = await start_listener(agent.config.discovery_port, agent.info)
        loops = asyncio.create_task(agent.run_loops())
        try:
            yield
        finally:
            agent._stop.set()
            loops.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await loops
            transport.close()
            await agent.stop()

    app = FastAPI(title=f"CrawlMesh Worker {agent.worker_id}", version=AGENT_VERSION, lifespan=lifespan)

    def _check_token(token: str | None) -> None:
        if not agent.config.token:
            return
        if token != agent.config.token:
            raise HTTPException(status_code=401, detail="Pairing token tidak valid")

    @app.get("/agent/info")
    async def agent_info(x_cluster_token: str | None = Header(default=None)):
        _check_token(x_cluster_token)
        return JSONResponse(agent.info())

    @app.get("/agent/health")
    async def agent_health():
        return {"status": "ok", "worker_id": agent.worker_id, "assigned": agent.assigned}

    @app.post("/agent/tasks/{task_id}/cancel")
    async def cancel_task(task_id: str):
        agent.active_tasks.pop(task_id, None)
        agent.inflight = max(0, agent.inflight - 1)
        return {"cancelled": True}

    return app


# ------------------------------------------------------------------- main
def build_config(argv: list[str] | None = None) -> AgentConfig:
    parser = argparse.ArgumentParser(description="CrawlMesh Worker Agent")
    parser.add_argument("--master", dest="master_url", help="Master base URL, e.g. http://192.168.1.10:8000")
    parser.add_argument("--token", help="Cluster pairing token from the master GUI")
    parser.add_argument("--port", type=int, help="Agent HTTP port (default 8010)")
    parser.add_argument("--name", dest="worker_name", help="Display name / hostname override")
    parser.add_argument("--pool-size", type=int, help="Multiprocessing worker count")
    parser.add_argument("--capacity", type=int, help="Concurrent task slots")
    parser.add_argument("--discovery-port", type=int, help="UDP discovery port (default 5599)")
    parser.add_argument("--state-dir", help="Where the stable worker id is stored")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved config and exit")
    args = parser.parse_args(argv)

    overrides: dict = {}
    for key in ("master_url", "token", "port", "worker_name", "pool_size", "capacity", "discovery_port"):
        value = getattr(args, key)
        if value:
            overrides[key] = value
    if args.state_dir:
        from pathlib import Path

        overrides["state_dir"] = Path(args.state_dir)

    config = AgentConfig(**overrides)
    if args.dry_run:
        print(json.dumps(config.model_dump(mode="json"), indent=2, default=str))
        print(json.dumps(ResourceMonitor.hardware(), indent=2))
        raise SystemExit(0)
    return config


def main(argv: list[str] | None = None) -> None:
    _configure_logging()
    config = build_config(argv)
    agent = WorkerAgent(config)
    app = create_app(agent)
    uvicorn.run(app, host="0.0.0.0", port=config.port, log_level="warning")


if __name__ == "__main__":
    main()
