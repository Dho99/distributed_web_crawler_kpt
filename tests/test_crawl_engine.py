from pathlib import Path

import pytest

from master.app.db.database import Database
from master.app.domain import aggregator, cluster as cluster_service, jobs, scheduler
from master.app.domain.hub import EventHub
from shared.models import (
    CrawlJobConfig,
    CrawlResultItem,
    HeartbeatRequest,
    JobStatus,
    RegisterRequest,
    TaskResultRequest,
    WorkerMetrics,
)

SEED = "http://127.0.0.1:9/bench/"
SECOND = "http://127.0.0.1:9/bench/2.html"


@pytest.fixture
async def env(tmp_path: Path):
    db = Database(tmp_path / "engine.db")
    await db.connect()
    hub = EventHub()
    await cluster_service.init_cluster(db, hub, name="Engine Test")
    await cluster_service.register_worker(
        db,
        hub,
        RegisterRequest(
            worker_id="worker-a",
            hostname="worker-a",
            ip_address="127.0.0.1",
            pool_size=2,
            capacity=2,
        ),
        5,
        15,
    )
    await cluster_service.assign_worker(db, hub, "worker-a")
    await cluster_service.heartbeat(
        db,
        hub,
        HeartbeatRequest(
            worker_id="worker-a",
            metrics=WorkerMetrics(cpu_usage=10, inflight=0, capacity=2),
        ),
    )
    yield db, hub
    await db.close()


def config(**overrides) -> CrawlJobConfig:
    data = {
        "job_name": "Engine",
        "seed_urls": [SEED],
        "maximum_pages": 10,
        "maximum_depth": 2,
        "batch_size": 2,
        "request_timeout": 5,
        "domain_delay": 0,
    }
    data.update(overrides)
    return CrawlJobConfig(**data)


async def test_job_decomposition_lease_and_aggregation(env):
    db, hub = env
    job = await jobs.create_job(db, hub, config())
    assert job.status == JobStatus.RUNNING
    assert job.pages_pending == 1

    created = await scheduler.decompose_once(db, hub)
    assert created == 1

    tasks = await db.fetch_all("SELECT * FROM tasks WHERE job_id=?", (job.job_id,))
    assert len(tasks) == 1
    assert tasks[0]["status"] == "queued"

    leased = await scheduler.lease_tasks(db, hub, "worker-a", 2)
    assert len(leased) == 1
    assert leased[0].urls == [SEED]
    node = await cluster_service.get_node(db, "worker-a")
    assert node is not None and node.inflight == 1

    result = TaskResultRequest(
        worker_id="worker-a",
        results=[
            CrawlResultItem(
                url=SEED,
                final_url=SEED,
                http_status=200,
                title="Bench",
                extracted_text="hello mesh",
                links=[SECOND],
                content_hash="abc",
                response_time_ms=12.5,
                size_bytes=1024,
            )
        ],
    )
    response = await aggregator.ingest_results(db, hub, leased[0].task_id, result)
    assert response.accepted == 1
    assert response.links_accepted == 1
    assert response.job_completed is False

    frontier = await db.fetch_all(
        "SELECT url, state, depth FROM frontier_urls WHERE job_id=? ORDER BY depth", (job.job_id,)
    )
    assert {row["state"] for row in frontier} == {"finished", "queued"}
    assert frontier[-1]["url"] == SECOND
    assert frontier[-1]["depth"] == 1

    node = await cluster_service.get_node(db, "worker-a")
    assert node is not None and node.inflight == 0 and node.completed_tasks >= 1


async def test_duplicate_result_is_idempotent(env):
    db, hub = env
    job = await jobs.create_job(db, hub, config(maximum_pages=1))
    await scheduler.decompose_once(db, hub)
    leased = await scheduler.lease_tasks(db, hub, "worker-a", 1)
    task_id = leased[0].task_id

    payload = TaskResultRequest(
        worker_id="worker-a",
        results=[
            CrawlResultItem(url=SEED, final_url=SEED, http_status=200, title="Bench", links=[])
        ],
    )
    first = await aggregator.ingest_results(db, hub, task_id, payload)
    assert first.accepted == 1

    # A retried task must not duplicate the result row.
    again = await aggregator.ingest_results(db, hub, task_id, payload)
    assert again.accepted == 0
    assert again.duplicates == 1

    count = await db.scalar("SELECT COUNT(*) FROM results WHERE job_id=?", (job.job_id,))
    assert count == 1

    job_after = await jobs.get_job(db, job.job_id)
    assert job_after is not None and job_after.status == JobStatus.COMPLETED


async def test_private_seed_requires_explicit_opt_in(env):
    db, hub = env
    with pytest.raises(ValueError):
        await jobs.create_job(
            db,
            hub,
            config(seed_urls=["http://192.168.1.50/private"], maximum_pages=1),
        )


async def test_static_mode_preassigns_worker(env):
    db, hub = env
    job = await jobs.create_job(db, hub, config(scheduling_mode="static"))
    await scheduler.decompose_once(db, hub)
    task = await db.fetch_one("SELECT assigned_worker FROM tasks WHERE job_id=?", (job.job_id,))
    assert task is not None and task["assigned_worker"] == "worker-a"

    # A different worker must not receive a statically assigned task.
    other = await scheduler.lease_tasks(db, hub, "worker-b", 2)
    assert other == []


async def test_frontier_budget_is_enforced(env):
    db, hub = env
    job = await jobs.create_job(db, hub, config(maximum_pages=5, seed_urls=[SEED]))
    row = await db.fetch_one("SELECT * FROM jobs WHERE job_id=?", (job.job_id,))

    from master.app.domain import frontier

    links = [(f"http://127.0.0.1:9/bench/{n}.html", 1) for n in range(30)]
    await frontier.enqueue_urls(db, row, links)
    total = await db.scalar("SELECT COUNT(*) FROM frontier_urls WHERE job_id=?", (job.job_id,))
    assert total == 5
