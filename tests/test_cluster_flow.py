from pathlib import Path

import pytest

from master.app.db.database import Database
from master.app.domain import cluster as cluster_service
from master.app.domain.hub import EventHub
from shared.models import (
    HeartbeatRequest,
    NodeStatus,
    RegisterRequest,
    WorkerMetrics,
)


@pytest.fixture
async def db(tmp_path: Path):
    database = Database(tmp_path / "test.db")
    await database.connect()
    yield database
    await database.close()


async def test_cluster_lifecycle(db: Database):
    hub = EventHub()
    assert await cluster_service.get_cluster(db) is None

    cluster = await cluster_service.init_cluster(db, hub, name="Test Cluster")
    assert cluster.cluster_id.startswith("CM-")
    assert cluster.pairing_token

    nodes = await cluster_service.list_nodes(db)
    assert [n.role.value for n in nodes] == ["master"]

    register = RegisterRequest(
        worker_id="worker-test-1",
        hostname="lab-pc-1",
        ip_address="192.168.1.21",
        port=8010,
        cpu_cores=8,
        memory_total=16 * 1024**3,
        os_name="Linux",
        python_version="3.12",
        agent_version="0.1.0",
        pool_size=4,
        capacity=4,
    )
    response = await cluster_service.register_worker(db, hub, register, 5, 15)
    assert response.accepted is True
    assert response.status == NodeStatus.PENDING

    beat = HeartbeatRequest(
        worker_id="worker-test-1",
        metrics=WorkerMetrics(cpu_usage=12.5, memory_usage=30.0, inflight=0, capacity=4),
    )
    result = await cluster_service.heartbeat(db, hub, beat)
    assert result.acknowledged is True
    assert result.assigned is False

    assigned = await cluster_service.assign_worker(db, hub, "worker-test-1")
    assert assigned is not None and assigned.status == NodeStatus.ONLINE

    result = await cluster_service.heartbeat(db, hub, beat)
    assert result.assigned is True
    assert result.status == NodeStatus.IDLE

    overview = await cluster_service.overview(db)
    assert overview.total_nodes == 2
    assert overview.active_workers == 1
    assert overview.total_cpu_cores >= 8

    failed = await cluster_service.set_worker_status(db, hub, "worker-test-1", NodeStatus.OFFLINE)
    assert failed is not None and failed.status == NodeStatus.OFFLINE

    # Simulated failure must survive heartbeats until the operator recovers it.
    result = await cluster_service.heartbeat(db, hub, beat)
    assert result.status == NodeStatus.OFFLINE
    assert result.assigned is False

    recovered = await cluster_service.set_worker_status(db, hub, "worker-test-1", NodeStatus.ONLINE)
    assert recovered is not None and recovered.status == NodeStatus.ONLINE

    removed = await cluster_service.remove_worker(db, hub, "worker-test-1")
    assert removed is not None
    assert removed.status == NodeStatus.REMOVED

    list_after = await cluster_service.list_nodes(db)
    assert all(node.worker_id != "worker-test-1" for node in list_after)


async def test_stale_worker_marked_offline(db: Database):
    hub = EventHub()
    await cluster_service.init_cluster(db, hub)
    await cluster_service.register_worker(
        db,
        hub,
        RegisterRequest(worker_id="worker-stale", hostname="stale", pool_size=2, capacity=2),
        5,
        15,
    )
    await cluster_service.assign_worker(db, hub, "worker-stale")
    await db.write(
        "UPDATE nodes SET last_heartbeat = '2000-01-01T00:00:00+00:00' WHERE worker_id = 'worker-stale'"
    )

    changed = await cluster_service.mark_stale_offline(db, hub, 15)
    assert changed == ["worker-stale"]
    node = await cluster_service.get_node(db, "worker-stale")
    assert node is not None and node.status == NodeStatus.OFFLINE
