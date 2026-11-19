from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from shared.models import (
    HeartbeatRequest,
    HeartbeatResponse,
    LeaseRequest,
    LeaseResponse,
    RegisterRequest,
    RegisterResponse,
    TaskFailRequest,
    TaskFailResponse,
    TaskResultRequest,
    TaskResultResponse,
    WorkerControl,
)

from ..core.config import Settings, get_settings
from ..db.database import Database
from ..domain import aggregator, cluster as cluster_service, scheduler
from ..domain.hub import EventHub
from .deps import get_db, get_hub, require_token

router = APIRouter(prefix="/api/worker", tags=["worker"])


@router.post("/register", response_model=RegisterResponse)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: Database = Depends(get_db),
    hub: EventHub = Depends(get_hub),
    settings: Settings = Depends(get_settings),
) -> RegisterResponse:
    await require_token(request, db)
    return await cluster_service.register_worker(
        db, hub, payload, settings.heartbeat_interval, settings.offline_threshold
    )


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def heartbeat(
    payload: HeartbeatRequest,
    request: Request,
    db: Database = Depends(get_db),
    hub: EventHub = Depends(get_hub),
) -> HeartbeatResponse:
    await require_token(request, db)
    return await cluster_service.heartbeat(db, hub, payload)


@router.post("/lease", response_model=LeaseResponse)
async def lease(
    payload: LeaseRequest,
    request: Request,
    db: Database = Depends(get_db),
    hub: EventHub = Depends(get_hub),
) -> LeaseResponse:
    await require_token(request, db)
    node = await cluster_service.get_node(db, payload.worker_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Worker tidak terdaftar")
    tasks = await scheduler.lease_tasks(db, hub, payload.worker_id, payload.free_slots)
    return LeaseResponse(tasks=tasks, control=WorkerControl())


@router.post("/tasks/{task_id}/result", response_model=TaskResultResponse)
async def task_result(
    task_id: str,
    payload: TaskResultRequest,
    request: Request,
    db: Database = Depends(get_db),
    hub: EventHub = Depends(get_hub),
) -> TaskResultResponse:
    await require_token(request, db)
    try:
        return await aggregator.ingest_results(db, hub, task_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task tidak ditemukan") from exc


@router.post("/tasks/{task_id}/fail", response_model=TaskFailResponse)
async def task_fail(
    task_id: str,
    payload: TaskFailRequest,
    request: Request,
    db: Database = Depends(get_db),
    hub: EventHub = Depends(get_hub),
) -> TaskFailResponse:
    await require_token(request, db)
    try:
        return await aggregator.fail_task(db, hub, task_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task tidak ditemukan") from exc
