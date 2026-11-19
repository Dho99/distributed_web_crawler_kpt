from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.models import ClusterInfo, DiscoveredNode

from ..core.config import Settings, get_settings
from ..core.net import local_ip
from ..db.database import Database, iso
from ..domain import cluster as cluster_service
from ..domain import discovery
from ..domain.hub import EventHub
from .deps import get_db, get_hub

router = APIRouter(prefix="/api/cluster", tags=["cluster"])


class InitRequest(BaseModel):
    name: str = "CrawlMesh Cluster"
    master_url: str | None = None


class DiscoverResponse(BaseModel):
    found: list[DiscoveredNode]
    scanned_ms: int
    already_known: list[str] = []


@router.post("/init", response_model=ClusterInfo)
async def init_cluster(
    payload: InitRequest | None = None,
    db: Database = Depends(get_db),
    hub: EventHub = Depends(get_hub),
    settings: Settings = Depends(get_settings),
) -> ClusterInfo:
    payload = payload or InitRequest()
    return await cluster_service.init_cluster(
        db,
        hub,
        name=payload.name,
        master_url=payload.master_url or f"http://{local_ip()}:{settings.port}",
        discovery_port=settings.discovery_port,
    )


@router.get("", response_model=ClusterInfo | None)
async def get_cluster(db: Database = Depends(get_db)) -> ClusterInfo | None:
    return await cluster_service.get_cluster(db)


@router.get("/overview")
async def get_overview(db: Database = Depends(get_db)):
    return await cluster_service.overview(db)


@router.post("/discover", response_model=DiscoverResponse)
async def discover_workers(
    db: Database = Depends(get_db),
    hub: EventHub = Depends(get_hub),
    settings: Settings = Depends(get_settings),
) -> DiscoverResponse:
    cluster = await cluster_service.get_cluster(db)
    found = await discovery.scan_network(
        port=settings.discovery_port,
        cluster_id=cluster.cluster_id if cluster else None,
        window_ms=settings.discovery_window_ms,
    )
    known_rows = await db.fetch_all("SELECT worker_id, status FROM nodes")
    known = {row["worker_id"]: row["status"] for row in known_rows}

    for node in found:
        status = known.get(node.worker_id)
        node.already_known = status is not None and status != "removed"
        if node.already_known:
            continue
        # Persist so ASSIGN AS WORKER can address the node immediately.
        now = iso()
        await db.write(
            """INSERT INTO nodes
               (worker_id, hostname, ip_address, port, role, status, cpu_cores, memory_total,
                os_name, python_version, agent_version, pool_size, capacity,
                last_heartbeat, registered_at, simulated_offline)
               VALUES (?, ?, ?, ?, 'worker', 'discovered', ?, ?, ?, ?, ?, ?, ?, NULL, ?, 0)
               ON CONFLICT (worker_id) DO UPDATE SET
                 hostname=excluded.hostname, ip_address=excluded.ip_address, port=excluded.port,
                 status='discovered', cpu_cores=excluded.cpu_cores,
                 memory_total=excluded.memory_total, os_name=excluded.os_name,
                 agent_version=excluded.agent_version, pool_size=excluded.pool_size,
                 capacity=excluded.capacity, removed_at=NULL""",
            (
                node.worker_id,
                node.hostname,
                node.ip_address,
                node.port,
                node.cpu_cores,
                node.memory_total,
                node.os_name,
                node.python_version,
                node.agent_version,
                max(1, node.cpu_cores - 1),
                max(1, node.cpu_cores - 1),
                now,
            ),
        )
        saved = await cluster_service.get_node(db, node.worker_id)
        if saved:
            await hub.broadcast("node.updated", saved.model_dump(mode="json"))

    return DiscoverResponse(
        found=found,
        scanned_ms=settings.discovery_window_ms,
        already_known=[n.worker_id for n in found if n.already_known],
    )
