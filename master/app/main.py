from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .api import bench as bench_api
from .api import cluster as cluster_api
from .api import experiments as experiments_api
from .api import health, jobs as jobs_api, nodes, worker, ws
from .core.config import get_settings
from .db.database import Database, iso
from .domain import cluster as cluster_service
from .domain import scheduler
from .domain.hub import EventHub

log = logging.getLogger("crawlmesh")


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
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


async def _offline_monitor(app: FastAPI) -> None:
    settings = get_settings()
    while True:
        try:
            await asyncio.sleep(2.0)
            changed = await cluster_service.mark_stale_offline(
                app.state.db, app.state.hub, settings.offline_threshold
            )
            for worker_id in changed:
                requeued = await scheduler.requeue_worker_tasks(
                    app.state.db, app.state.hub, worker_id
                )
                await app.state.hub.broadcast(
                    "worker.failed",
                    {
                        "worker_id": worker_id,
                        "detected_at": iso(),
                        "affected_tasks": requeued,
                    },
                )
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - keep monitor alive
            log.exception("offline monitor error")


async def _scheduler_loop(app: FastAPI) -> None:
    while True:
        try:
            await asyncio.sleep(0.5)
            result = await scheduler.tick(app.state.db, app.state.hub)
            if result["decomposed"] or result["completed_jobs"]:
                log.info("scheduler tick %s", result)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - keep scheduler alive
            log.exception("scheduler loop error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    settings = get_settings()
    db = Database(settings.db_path)
    await db.connect()
    app.state.db = db
    app.state.hub = EventHub()
    monitor = asyncio.create_task(_offline_monitor(app))
    ticker = asyncio.create_task(_scheduler_loop(app))
    log.info("CrawlMesh master ready db=%s", settings.db_path)
    try:
        yield
    finally:
        monitor.cancel()
        ticker.cancel()
        for task in (monitor, ticker):
            try:
                await task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
        await db.close()


settings = get_settings()
app = FastAPI(title="CrawlMesh Master", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(cluster_api.router)
app.include_router(nodes.router)
app.include_router(jobs_api.router)
app.include_router(worker.router)
app.include_router(ws.router)
app.include_router(bench_api.router)
app.include_router(experiments_api.router)


@app.get("/robots.txt", include_in_schema=False)
async def root_robots():
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse("User-agent: *\nAllow: /\n")


def _mount_spa(application: FastAPI, static_dir: Path) -> None:
    @application.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        index = static_dir / "index.html"
        if not index.exists():
            return JSONResponse(
                {
                    "detail": "GUI belum dibangun. Jalankan: cd web && npm install && npm run build",
                    "expected": str(index),
                },
                status_code=503,
            )
        candidate = (static_dir / full_path).resolve()
        if full_path and candidate.is_file() and static_dir.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(index)


_mount_spa(app, settings.static_dir)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "master.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
