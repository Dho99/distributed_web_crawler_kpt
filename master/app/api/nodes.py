from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shared.models import NodeOut, NodeStatus, RegisterRequest

from ..db.database import Database
from ..domain import cluster as cluster_service
from ..domain.hub import EventHub
from .deps import get_db, get_hub

router = APIRouter(prefix="/api/nodes", tags=["nodes"])


class ManualAddRequest(BaseModel):
    ip_address: str
    port: int = 8010


@router.get("", response_model=list[NodeOut])
async def list_nodes(db: Database = Depends(get_db)) -> list[NodeOut]:
    return await cluster_service.list_nodes(db)


@router.get("/{worker_id}", response_model=NodeOut)
async def get_node(worker_id: str, db: Database = Depends(get_db)) -> NodeOut:
    node = await cluster_service.get_node(db, worker_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node tidak ditemukan")
    return node


@router.post("/{worker_id}/assign", response_model=NodeOut)
async def assign_worker(
    worker_id: str, db: Database = Depends(get_db), hub: EventHub = Depends(get_hub)
) -> NodeOut:
    node = await cluster_service.assign_worker(db, hub, worker_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node worker tidak ditemukan")
    return node


@router.post("/{worker_id}/remove", response_model=NodeOut)
async def remove_worker(
    worker_id: str, db: Database = Depends(get_db), hub: EventHub = Depends(get_hub)
) -> NodeOut:
    node = await cluster_service.remove_worker(db, hub, worker_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node worker tidak ditemukan")
    return node


@router.post("/{worker_id}/simulate-failure", response_model=NodeOut)
async def simulate_failure(
    worker_id: str, db: Database = Depends(get_db), hub: EventHub = Depends(get_hub)
) -> NodeOut:
    node = await cluster_service.set_worker_status(db, hub, worker_id, NodeStatus.OFFLINE)
    if node is None:
        raise HTTPException(status_code=404, detail="Node worker tidak ditemukan")
    await hub.broadcast("failure.simulated", {"worker_id": worker_id})
    return node


@router.post("/{worker_id}/recover", response_model=NodeOut)
async def recover_worker(
    worker_id: str, db: Database = Depends(get_db), hub: EventHub = Depends(get_hub)
) -> NodeOut:
    node = await cluster_service.set_worker_status(db, hub, worker_id, NodeStatus.ONLINE)
    if node is None:
        raise HTTPException(status_code=404, detail="Node worker tidak ditemukan")
    return node


@router.post("/manual", response_model=NodeOut, status_code=201)
async def add_manual(
    payload: ManualAddRequest,
    db: Database = Depends(get_db),
    hub: EventHub = Depends(get_hub),
) -> NodeOut:
    cluster = await cluster_service.get_cluster(db)
    if cluster is None:
        raise HTTPException(status_code=409, detail="Master belum diinisialisasi")

    url = f"http://{payload.ip_address}:{payload.port}/agent/info"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(url, headers={"X-Cluster-Token": cluster.pairing_token})
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Agent tidak dapat dihubungi: {exc}") from exc

    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="Token agent tidak cocok dengan cluster")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Agent membalas HTTP {resp.status_code}")

    info = resp.json()
    req = RegisterRequest(
        worker_id=info.get("worker_id"),
        hostname=info.get("hostname", payload.ip_address),
        ip_address=payload.ip_address,
        port=payload.port,
        cpu_cores=int(info.get("cpu_cores", 1)),
        memory_total=int(info.get("memory_total", 0)),
        os_name=info.get("os_name", ""),
        python_version=info.get("python_version", ""),
        agent_version=info.get("agent_version", ""),
        pool_size=int(info.get("pool_size", 1)),
        capacity=int(info.get("pool_size", 1)),
    )
    result = await cluster_service.register_worker(
        db, hub, req, heartbeat_interval=5, offline_threshold=15
    )
    node = await cluster_service.get_node(db, result.worker_id)
    if node is None:
        raise HTTPException(status_code=500, detail="Gagal menyimpan node")
    return node
