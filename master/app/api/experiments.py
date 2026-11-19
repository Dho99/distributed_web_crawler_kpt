from __future__ import annotations

import csv
import io
import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..core.config import Settings, get_settings
from ..db.database import Database
from ..domain import experiments as experiment_service
from ..domain.experiments import RunSpec
from ..domain.hub import EventHub
from .deps import get_db, get_hub

router = APIRouter(prefix="/api/experiments", tags=["experiments"])

ExperimentType = Literal[
    "sequential",
    "local_parallel",
    "distributed",
    "scalability",
    "load_balancing",
    "fault_tolerance",
]


class RunRequest(BaseModel):
    experiment_type: ExperimentType = "distributed"
    worker_count: int = Field(default=0, ge=0, le=64)
    seed_urls: list[str] | None = None
    maximum_pages: int = Field(default=60, ge=1, le=2000)
    maximum_depth: int = Field(default=1, ge=0, le=10)
    batch_size: int = Field(default=5, ge=1, le=100)
    request_timeout: float = Field(default=10.0, gt=0, le=120)
    domain_delay: float = Field(default=0.02, ge=0, le=10)
    scheduling_mode: Literal["static", "dynamic"] = "dynamic"
    repeat: int = Field(default=3, ge=1, le=7)


@router.get("/busy")
async def busy() -> dict[str, bool]:
    return {"running": experiment_service.is_running()}


@router.post("/run", status_code=201)
async def run_experiment(
    payload: RunRequest,
    db: Database = Depends(get_db),
    hub: EventHub = Depends(get_hub),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    from shared.netinfo import local_ip

    if payload.experiment_type in ("fault_tolerance", "load_balancing"):
        raise HTTPException(
            status_code=400,
            detail=(
                "Mode ini dijalankan dari halaman Crawl Jobs + simulasi failure pada Cluster, "
                "bukan lewat runner benchmark."
            ),
        )

    seeds = payload.seed_urls or [f"http://{local_ip()}:{settings.port}/bench/"]
    worker_count = payload.worker_count
    if payload.experiment_type == "sequential":
        worker_count = 1
    elif payload.experiment_type == "local_parallel" and worker_count <= 0:
        worker_count = 4
    elif payload.experiment_type == "distributed" and worker_count <= 0:
        worker_count = len(await experiment_service._active_worker_ids(db)) or 1

    spec = RunSpec(
        experiment_type=payload.experiment_type,
        worker_count=worker_count,
        seed_urls=seeds,
        maximum_pages=payload.maximum_pages,
        maximum_depth=payload.maximum_depth,
        batch_size=payload.batch_size,
        request_timeout=payload.request_timeout,
        domain_delay=payload.domain_delay,
        scheduling_mode=payload.scheduling_mode,
        repeat=payload.repeat,
    )
    try:
        return await experiment_service.start(db, hub, spec)
    except experiment_service.ExperimentBusy as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
async def list_experiments(
    limit: int = Query(default=100, ge=1, le=500),
    group_id: str | None = None,
    db: Database = Depends(get_db),
) -> list[dict[str, Any]]:
    return await experiment_service.list_experiments(db, limit, group_id)


@router.get("/export")
async def export_experiments(
    format: Literal["csv", "json"] = "csv",
    db: Database = Depends(get_db),
) -> Response:
    rows = await experiment_service.list_experiments(db, limit=500)
    headers = {"Content-Disposition": f'attachment; filename="crawlmesh-experiments.{format}"'}
    if format == "json":
        return Response(json.dumps(rows, indent=2, default=str), media_type="application/json", headers=headers)

    buffer = io.StringIO()
    fields = [
        "experiment_id",
        "experiment_type",
        "worker_count",
        "scheduling_mode",
        "status",
        "execution_time_ms",
        "pages_ok",
        "pages_failed",
        "speedup",
        "efficiency",
        "throughput",
        "cpu_utilization",
        "memory_utilization",
        "recovery_time_ms",
        "group_id",
        "created_at",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return Response(buffer.getvalue(), media_type="text/csv", headers=headers)


@router.get("/{experiment_id}")
async def get_experiment(
    experiment_id: str,
    samples: bool = Query(default=False),
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    row = await experiment_service.get_experiment(db, experiment_id, with_samples=samples)
    if row is None:
        raise HTTPException(status_code=404, detail="Eksperimen tidak ditemukan")
    return row


@router.post("/{experiment_id}/cancel")
async def cancel_experiment(
    experiment_id: str,
    db: Database = Depends(get_db),
    hub: EventHub = Depends(get_hub),
) -> dict[str, Any] | None:
    row = await experiment_service.get_experiment(db, experiment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Eksperimen tidak ditemukan")
    return await experiment_service.cancel(db, hub, experiment_id)
