from __future__ import annotations

import logging
import platform
import secrets
import socket
import uuid
from datetime import datetime, timedelta, timezone

import psutil

from shared.models import (
    ClusterInfo,
    HeartbeatRequest,
    HeartbeatResponse,
    JobStatus,
    NodeOut,
    NodeRole,
    NodeStatus,
    OverviewOut,
    RegisterRequest,
    RegisterResponse,
    WorkerControl,
)

from ..core.net import local_ip
from ..db.database import Database, iso, load, parse_dt, utcnow
from .hub import EventHub

log = logging.getLogger("crawlmesh.cluster")

MASTER_WORKER_ID = "master"


def _node_out(row: dict) -> NodeOut:
    return NodeOut(
        worker_id=row["worker_id"],
        hostname=row["hostname"],
        ip_address=row["ip_address"],
        port=row["port"],
        role=NodeRole(row["role"]),
        status=NodeStatus(row["status"]),
        cpu_cores=row["cpu_cores"],
        memory_total=row["memory_total"],
        os_name=row["os_name"],
        python_version=row["python_version"],
        pool_size=row["pool_size"],
        agent_version=row["agent_version"],
        last_heartbeat=parse_dt(row["last_heartbeat"]),
        registered_at=parse_dt(row["registered_at"]),
        cpu_usage=row["cpu_usage"],
        memory_usage=row["memory_usage"],
        active_tasks=row["active_tasks"],
        completed_tasks=row["completed_tasks"],
        failed_tasks=row["failed_tasks"],
        child_processes=row["child_processes"],
        inflight=row["inflight"],
        capacity=row["capacity"],
        throughput=row["throughput"],
    )


def cluster_from_row(row: dict) -> ClusterInfo:
    return ClusterInfo(
        cluster_id=row["cluster_id"],
        name=row["name"],
        pairing_token=row["pairing_token"],
        master_url=row["master_url"],
        discovery_port=row["discovery_port"],
        created_at=parse_dt(row["created_at"]) or utcnow(),
    )


async def get_cluster(db: Database) -> ClusterInfo | None:
    row = await db.fetch_one("SELECT * FROM cluster WHERE id = 1")
    return cluster_from_row(row) if row else None


async def init_cluster(
    db: Database,
    hub: EventHub,
    name: str = "CrawlMesh Cluster",
    master_url: str | None = None,
    discovery_port: int = 5599,
) -> ClusterInfo:
    existing = await get_cluster(db)
    if existing:
        return existing

    cluster_id = f"CM-{secrets.token_hex(3).upper()}"
    token = secrets.token_urlsafe(24)
    url = master_url or f"http://{local_ip()}:8000"

    await db.write(
        """INSERT INTO cluster (id, cluster_id, name, pairing_token, master_url, discovery_port, created_at)
           VALUES (1, ?, ?, ?, ?, ?, ?)""",
        (cluster_id, name, token, url, discovery_port, iso()),
    )

    hostname = socket.gethostname()
    await db.write(
        """INSERT OR REPLACE INTO nodes
           (worker_id, hostname, ip_address, port, role, status, cpu_cores, memory_total,
            os_name, python_version, agent_version, pool_size, capacity,
            last_heartbeat, registered_at)
           VALUES (?, ?, ?, ?, 'master', 'online', ?, ?, ?, ?, '0.1.0', ?, ?, ?, ?)""",
        (
            MASTER_WORKER_ID,
            hostname,
            local_ip(),
            8000,
            psutil.cpu_count(logical=True) or 1,
            psutil.virtual_memory().total,
            f"{platform.system()} {platform.release()}",
            platform.python_version(),
            psutil.cpu_count(logical=False) or 1,
            psutil.cpu_count(logical=False) or 1,
            iso(),
            iso(),
        ),
    )

    cluster = await get_cluster(db)
    assert cluster is not None
    await hub.broadcast("cluster.initialized", cluster.model_dump(mode="json"))
    await hub.broadcast("node.updated", {"worker_id": MASTER_WORKER_ID, "status": "online"})
    log.info("cluster initialised: %s", cluster_id)
    return cluster


async def list_nodes(db: Database) -> list[NodeOut]:
    rows = await db.fetch_all(
        "SELECT * FROM nodes WHERE status != 'removed' ORDER BY role DESC, hostname ASC"
    )
    return [_node_out(row) for row in rows]


async def get_node(db: Database, worker_id: str) -> NodeOut | None:
    row = await db.fetch_one("SELECT * FROM nodes WHERE worker_id = ?", (worker_id,))
    return _node_out(row) if row else None


async def overview(db: Database) -> OverviewOut:
    cluster = await get_cluster(db)
    nodes = await list_nodes(db)
    workers = [n for n in nodes if n.role == NodeRole.WORKER]
    active = [n for n in workers if n.status not in (NodeStatus.OFFLINE, NodeStatus.PENDING)]
    offline = [n for n in workers if n.status == NodeStatus.OFFLINE]

    running_jobs = await db.scalar(
        "SELECT COUNT(*) FROM jobs WHERE status = ?", (JobStatus.RUNNING.value,)
    )
    pages = await db.scalar("SELECT COUNT(*) FROM results WHERE error IS NULL")
    failed = await db.scalar(
        "SELECT COUNT(*) FROM tasks WHERE status IN ('failed','dead')"
    )
    per_sec = await db.scalar(
        """SELECT COUNT(*) FROM results
           WHERE crawled_at >= ?""",
        ((utcnow() - timedelta(seconds=10)).isoformat(),),
    )
    pending = await db.scalar(
        "SELECT COUNT(*) FROM frontier_urls WHERE state = 'queued'"
    )

    return OverviewOut(
        cluster=cluster,
        total_nodes=len(nodes),
        active_workers=len(active),
        offline_workers=len(offline),
        total_cpu_cores=sum(n.cpu_cores for n in nodes),
        total_memory=sum(n.memory_total for n in nodes),
        running_jobs=running_jobs,
        pages_crawled=pages,
        failed_tasks=failed,
        current_throughput=round(float(per_sec) / 10.0, 2),
        nodes=nodes,
    )


async def _upsert_node(db: Database, req: RegisterRequest, worker_id: str) -> dict:
    existing = await db.fetch_one("SELECT * FROM nodes WHERE worker_id = ?", (worker_id,))
    now = iso()
    if existing:
        await db.write(
            """UPDATE nodes SET hostname=?, ip_address=?, port=?, cpu_cores=?, memory_total=?,
                   os_name=?, python_version=?, agent_version=?, pool_size=?, capacity=?,
                   last_heartbeat=?, removed_at=NULL
               WHERE worker_id=?""",
            (
                req.hostname,
                req.ip_address,
                req.port,
                req.cpu_cores,
                req.memory_total,
                req.os_name,
                req.python_version,
                req.agent_version,
                req.pool_size,
                req.capacity,
                now,
                worker_id,
            ),
        )
    else:
        await db.write(
            """INSERT INTO nodes
               (worker_id, hostname, ip_address, port, role, status, cpu_cores, memory_total,
                os_name, python_version, agent_version, pool_size, capacity,
                last_heartbeat, registered_at)
               VALUES (?, ?, ?, ?, 'worker', 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                worker_id,
                req.hostname,
                req.ip_address,
                req.port,
                req.cpu_cores,
                req.memory_total,
                req.os_name,
                req.python_version,
                req.agent_version,
                req.pool_size,
                req.capacity,
                now,
                now,
            ),
        )
    row = await db.fetch_one("SELECT * FROM nodes WHERE worker_id = ?", (worker_id,))
    return row or {}


async def register_worker(
    db: Database, hub: EventHub, req: RegisterRequest, heartbeat_interval: int, offline_threshold: int
) -> RegisterResponse:
    cluster = await get_cluster(db)
    if cluster is None:
        return RegisterResponse(
            worker_id=req.worker_id or "",
            cluster_id="",
            status=NodeStatus.PENDING,
            accepted=False,
            message="Master belum diinisialisasi",
        )

    worker_id = req.worker_id or f"worker-{req.hostname.lower()}-{uuid.uuid4().hex[:6]}"
    row = await _upsert_node(db, req, worker_id)
    status = NodeStatus(row.get("status", "pending"))
    node = _node_out(row)

    await hub.broadcast("node.updated", node.model_dump(mode="json"))
    return RegisterResponse(
        worker_id=worker_id,
        cluster_id=cluster.cluster_id,
        status=status,
        accepted=True,
        heartbeat_interval=heartbeat_interval,
        offline_threshold=offline_threshold,
        message="Worker terdaftar. Menunggu assignment dari operator.",
    )


async def heartbeat(db: Database, hub: EventHub, req: HeartbeatRequest) -> HeartbeatResponse:
    row = await db.fetch_one("SELECT * FROM nodes WHERE worker_id = ?", (req.worker_id,))
    if row is None:
        return HeartbeatResponse(acknowledged=False, message="unknown worker")

    m = req.metrics
    current = NodeStatus(row["status"])
    now = iso()

    if row["simulated_offline"]:
        new_status = NodeStatus.OFFLINE
    elif current in (NodeStatus.PENDING, NodeStatus.DISCOVERED, NodeStatus.REMOVED):
        new_status = NodeStatus.PENDING
    elif current == NodeStatus.OFFLINE:
        new_status = NodeStatus.ONLINE
    else:
        new_status = NodeStatus.BUSY if m.inflight > 0 else NodeStatus.IDLE

    await db.write(
        """UPDATE nodes SET status=?, cpu_usage=?, memory_usage=?, active_tasks=?, child_processes=?,
               inflight=?, capacity=?, throughput=?, last_heartbeat=?
           WHERE worker_id=?""",
        (
            new_status.value,
            m.cpu_usage,
            m.memory_usage,
            m.active_tasks,
            m.child_processes,
            m.inflight,
            m.capacity,
            m.throughput,
            now,
            req.worker_id,
        ),
    )
    await db.write(
        """INSERT INTO worker_metrics
           (worker_id, cpu_usage, memory_usage, active_processes, child_processes, active_tasks, throughput, recorded_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            req.worker_id,
            m.cpu_usage,
            m.memory_usage,
            m.active_processes,
            m.child_processes,
            m.active_tasks,
            m.throughput,
            now,
        ),
    )

    assigned = new_status in (
        NodeStatus.ONLINE,
        NodeStatus.IDLE,
        NodeStatus.BUSY,
        NodeStatus.DEGRADED,
    )
    node = await get_node(db, req.worker_id)
    if node:
        await hub.broadcast("node.updated", node.model_dump(mode="json"))

    paused_rows = await db.fetch_all("SELECT job_id FROM jobs WHERE status = 'paused'")
    return HeartbeatResponse(
        acknowledged=True,
        assigned=assigned,
        status=new_status,
        control=WorkerControl(
            paused_job_ids=[r["job_id"] for r in paused_rows],
            server_time=utcnow(),
        ),
    )


async def assign_worker(db: Database, hub: EventHub, worker_id: str) -> NodeOut | None:
    row = await db.fetch_one("SELECT * FROM nodes WHERE worker_id = ?", (worker_id,))
    if row is None or row["role"] != "worker":
        return None
    await db.write(
        "UPDATE nodes SET status='online', removed_at=NULL, simulated_offline=0, "
        "registered_at=COALESCE(registered_at, ?) WHERE worker_id=?",
        (iso(), worker_id),
    )
    node = await get_node(db, worker_id)
    if node:
        await hub.broadcast("node.updated", node.model_dump(mode="json"))
    log.info("worker assigned: %s", worker_id)
    return node


async def remove_worker(db: Database, hub: EventHub, worker_id: str) -> NodeOut | None:
    row = await db.fetch_one("SELECT * FROM nodes WHERE worker_id = ?", (worker_id,))
    if row is None or row["role"] != "worker":
        return None
    await db.write(
        "UPDATE nodes SET status='removed', inflight=0, removed_at=?, last_heartbeat=? WHERE worker_id=?",
        (iso(), iso(), worker_id),
    )
    node = await get_node(db, worker_id)
    if node:
        await hub.broadcast("node.removed", {"worker_id": worker_id})
    return node


async def set_worker_status(db: Database, hub: EventHub, worker_id: str, status: NodeStatus) -> NodeOut | None:
    row = await db.fetch_one("SELECT * FROM nodes WHERE worker_id = ?", (worker_id,))
    if row is None or row["role"] != "worker":
        return None
    simulated = 1 if status not in (NodeStatus.ONLINE, NodeStatus.IDLE) else 0
    await db.write(
        "UPDATE nodes SET status=?, simulated_offline=? WHERE worker_id=?",
        (status.value, simulated, worker_id),
    )
    node = await get_node(db, worker_id)
    if node:
        await hub.broadcast("node.updated", node.model_dump(mode="json"))
    return node


async def mark_stale_offline(db: Database, hub: EventHub, threshold_seconds: int) -> list[str]:
    cutoff = (utcnow() - timedelta(seconds=threshold_seconds)).isoformat()
    rows = await db.fetch_all(
        """SELECT worker_id FROM nodes
           WHERE role='worker'
             AND status NOT IN ('offline','removed','pending','discovered')
             AND (last_heartbeat IS NULL OR last_heartbeat < ?)""",
        (cutoff,),
    )
    changed: list[str] = []
    for row in rows:
        worker_id = row["worker_id"]
        await db.write(
            "UPDATE nodes SET status='offline', inflight=0, cpu_usage=0, memory_usage=0, active_tasks=0 WHERE worker_id=?",
            (worker_id,),
        )
        changed.append(worker_id)
        await hub.broadcast("node.offline", {"worker_id": worker_id, "detected_at": iso()})
        log.warning("worker offline: %s", worker_id)
    return changed


def node_meta(row: dict) -> dict:
    return load(row.get("meta"))


def now_dt() -> datetime:
    return datetime.now(timezone.utc)
