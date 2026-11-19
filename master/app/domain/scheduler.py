from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

from shared.models import JobStatus, LeaseTask, SchedulingMode, TaskStatus

from ..db.database import Database, iso, load, parse_dt
from . import jobs
from .hub import EventHub

log = logging.getLogger("crawlmesh.scheduler")

_lease_lock = asyncio.Lock()
ACTIVE_STATUSES = ("online", "idle", "busy")
QUEUED_TASK_LIMIT_PER_SLOT = 2


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _active_workers(db: Database) -> list[dict]:
    return await db.fetch_all(
        "SELECT * FROM nodes WHERE role='worker' AND status IN (?,?,?) AND simulated_offline = 0",
        ACTIVE_STATUSES,
    )


async def decompose_job(
    db: Database,
    hub: EventHub,
    job: dict,
    workers: list[dict],
    total_capacity: int | None = None,
    max_tasks: int = 16,
) -> int:
    """Turn queued frontier rows of one job into tasks (up to max_tasks)."""
    allowed = load(job.get("worker_allowlist"), [])
    eligible = [w for w in workers if not allowed or w["worker_id"] in allowed]
    capacity = total_capacity or max(1, sum(int(w["capacity"] or 1) for w in eligible) or 1)
    limit = capacity * QUEUED_TASK_LIMIT_PER_SLOT

    created = 0
    for _ in range(max(1, max_tasks)):
        queued_tasks = await db.scalar(
            "SELECT COUNT(*) FROM tasks WHERE job_id=? AND status='queued'", (job["job_id"],)
        )
        if int(queued_tasks) >= limit:
            break

        rows = await db.fetch_all(
            """SELECT id, url, depth, priority FROM frontier_urls
               WHERE job_id=? AND state='queued'
               ORDER BY priority DESC, id ASC LIMIT ?""",
            (job["job_id"], int(job["batch_size"])),
        )
        if not rows:
            break

        task_total = await db.scalar(
            "SELECT COUNT(*) FROM tasks WHERE job_id=?", (job["job_id"],)
        )
        if job["scheduling_mode"] == SchedulingMode.STATIC.value and eligible:
            assigned = eligible[int(task_total) % len(eligible)]["worker_id"]
        else:
            assigned = None

        task_id = f"task-{job['job_id'][4:]}-{int(task_total) + 1:05d}"
        urls = [row["url"] for row in rows]
        depth = max(int(row["depth"]) for row in rows)
        now = iso()

        await db.write(
            """INSERT INTO tasks
               (task_id, job_id, depth, urls, url_count, priority, assigned_worker,
                attempt_count, max_attempts, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0, 3, 'queued', ?)""",
            (
                task_id,
                job["job_id"],
                depth,
                json.dumps(urls),
                len(urls),
                max(int(row["priority"]) for row in rows),
                assigned,
                now,
            ),
        )
        await db.write_many(
            "UPDATE frontier_urls SET state='scheduled', scheduled_at=? WHERE id=?",
            [(now, row["id"]) for row in rows],
        )
        await db.write(
            """INSERT INTO task_events (task_id, job_id, worker_id, event, detail, created_at)
               VALUES (?, ?, ?, 'created', ?, ?)""",
            (task_id, job["job_id"], assigned, f"{len(urls)} urls", now),
        )
        created += 1

    if created:
        await hub.broadcast("scheduler.tick", {"tasks_created": created, "job_id": job["job_id"]})
    return created


async def decompose_once(db: Database, hub: EventHub) -> int:
    workers = await _active_workers(db)
    if not workers:
        return 0

    job_rows = await db.fetch_all(
        "SELECT * FROM jobs WHERE status = ? AND mode = 'distributed'",
        (JobStatus.RUNNING.value,),
    )
    total_capacity = max(1, sum(int(w["capacity"] or 1) for w in workers))
    created = 0
    for job in job_rows:
        created += await decompose_job(db, hub, job, workers, total_capacity)
    return created


async def lease_tasks(
    db: Database, hub: EventHub, worker_id: str, free_slots: int
) -> list[LeaseTask]:
    async with _lease_lock:
        node = await db.fetch_one("SELECT * FROM nodes WHERE worker_id=?", (worker_id,))
        if node is None:
            return []
        mode = node["role"]
        if mode != "worker":
            return []
        if node["status"] not in ACTIVE_STATUSES or node["simulated_offline"]:
            return []
        if (node["last_heartbeat"] or "") < (utc_iso(offset=-30)):
            return []

        capacity = int(node["capacity"] or 1)
        inflight = int(node["inflight"] or 0)
        room = max(0, capacity - inflight)
        grant = min(int(free_slots), room)
        if grant <= 0:
            return []

        # Dynamic mode: do not hand work to a hot worker. Static mode keeps the
        # pre-assigned share, which is the point of the comparison experiment.
        if float(node["cpu_usage"] or 0) > 92:
            return []

        rows = await db.fetch_all(
            """SELECT t.*, j.request_timeout, j.domain_delay, j.respect_robots, j.user_agent,
                      j.allow_private_targets, j.maximum_depth
               FROM tasks t JOIN jobs j ON j.job_id = t.job_id
               WHERE t.status='queued' AND j.status='running'
                 AND (t.assigned_worker IS NULL OR t.assigned_worker = ?)
                 AND (j.scheduling_mode = 'dynamic' OR t.assigned_worker = ?)
                 AND (j.worker_allowlist = '[]'
                      OR EXISTS (SELECT 1 FROM json_each(j.worker_allowlist) WHERE json_each.value = ?))
               ORDER BY t.priority DESC, t.created_at ASC, t.task_id ASC
               LIMIT ?""",
            (worker_id, worker_id, worker_id, grant),
        )
        if not rows:
            return []

        now = _now()
        leased: list[LeaseTask] = []
        for row in rows:
            urls = json.loads(row["urls"])
            deadline = now + timedelta(
                seconds=float(row["request_timeout"]) * max(1, len(urls)) + 60
            )
            await db.write(
                """UPDATE tasks
                   SET status='leased', assigned_worker=?, attempt_count=attempt_count+1,
                       leased_at=?, lease_deadline=?
                   WHERE task_id=?""",
                (worker_id, now.isoformat(), deadline.isoformat(), row["task_id"]),
            )
            await db.write(
                """INSERT INTO task_events (task_id, job_id, worker_id, event, detail, created_at)
                   VALUES (?, ?, ?, 'leased', ?, ?)""",
                (
                    row["task_id"],
                    row["job_id"],
                    worker_id,
                    f"attempt {int(row['attempt_count']) + 1}",
                    now.isoformat(),
                ),
            )
            leased.append(
                LeaseTask(
                    task_id=row["task_id"],
                    job_id=row["job_id"],
                    urls=urls,
                    depth=int(row["depth"]),
                    attempt=int(row["attempt_count"]) + 1,
                    request_timeout=float(row["request_timeout"]),
                    domain_delay=float(row["domain_delay"]),
                    respect_robots=bool(row["respect_robots"]),
                    user_agent=row["user_agent"],
                    allow_private_targets=bool(row["allow_private_targets"]),
                )
            )

        await db.write(
            "UPDATE nodes SET inflight = inflight + ?, status='busy' WHERE worker_id=?",
            (len(leased), worker_id),
        )
        await hub.broadcast(
            "task.leased",
            {"worker_id": worker_id, "task_ids": [t.task_id for t in leased]},
        )
        return leased


def utc_iso(offset: int = 0) -> str:
    return (_now() + timedelta(seconds=offset)).isoformat()


async def _release_lease(db: Database, task: dict, reason: str) -> str:
    """Requeue or dead-letter a leased task. Returns the resulting status."""
    attempt = int(task["attempt_count"] or 0)
    max_attempts = int(task["max_attempts"] or 3)
    now = iso()

    worker_id = task["assigned_worker"]
    if worker_id:
        await db.write(
            "UPDATE nodes SET inflight = MAX(0, inflight - 1), failed_tasks = failed_tasks + 1 WHERE worker_id=?",
            (worker_id,),
        )

    if attempt >= max_attempts:
        new_status = TaskStatus.DEAD.value
        await db.write(
            "UPDATE tasks SET status=?, failed_at=?, error=?, completed_at=? WHERE task_id=?",
            (new_status, now, reason, now, task["task_id"]),
        )
        from shared.urlnorm import url_hash

        for url in load(task["urls"], []):
            await db.write(
                "UPDATE frontier_urls SET state='failed', finished_at=? WHERE job_id=? AND url_hash=? AND state='scheduled'",
                (now, task["job_id"], url_hash(url)),
            )
    else:
        new_status = TaskStatus.QUEUED.value
        await db.write(
            """UPDATE tasks SET status='queued', assigned_worker=NULL, error=?,
                   leased_at=NULL, lease_deadline=NULL WHERE task_id=?""",
            (reason, task["task_id"]),
        )
        urls = json.loads(task["urls"])
        from shared.urlnorm import url_hash

        await db.write_many(
            "UPDATE frontier_urls SET state='queued', scheduled_at=NULL WHERE job_id=? AND url_hash=? AND state='scheduled'",
            [(task["job_id"], url_hash(url)) for url in urls],
        )

    await db.write(
        "INSERT INTO task_events (task_id, job_id, worker_id, event, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (task["task_id"], task["job_id"], worker_id, new_status, reason, now),
    )
    return new_status


async def requeue_expired(db: Database, hub: EventHub) -> int:
    now = _now().isoformat()
    rows = await db.fetch_all(
        """SELECT * FROM tasks
           WHERE status IN ('leased','running') AND lease_deadline IS NOT NULL AND lease_deadline < ?""",
        (now,),
    )
    for task in rows:
        status = await _release_lease(db, task, "lease timeout")
        await hub.broadcast(
            "task.requeued",
            {"task_id": task["task_id"], "worker_id": task["assigned_worker"], "status": status},
        )
    return len(rows)


async def requeue_worker_tasks(db: Database, hub: EventHub, worker_id: str) -> int:
    rows = await db.fetch_all(
        "SELECT * FROM tasks WHERE assigned_worker=? AND status IN ('leased','running')",
        (worker_id,),
    )
    for task in rows:
        status = await _release_lease(db, task, f"worker {worker_id} offline")
        await hub.broadcast(
            "task.requeued",
            {"task_id": task["task_id"], "worker_id": worker_id, "status": status},
        )
    return len(rows)


async def finish_task(
    db: Database, hub: EventHub, task_id: str, worker_id: str | None = None
) -> dict | None:
    task = await db.fetch_one("SELECT * FROM tasks WHERE task_id=?", (task_id,))
    if task is None:
        return None
    if task["status"] == TaskStatus.COMPLETED.value:
        return task

    now = iso()
    await db.write(
        "UPDATE tasks SET status='completed', completed_at=?, error=NULL WHERE task_id=?",
        (now, task_id),
    )
    from shared.urlnorm import url_hash

    await db.write_many(
        """UPDATE frontier_urls SET state='finished', finished_at=?
           WHERE job_id=? AND url_hash=? AND state='scheduled'""",
        [(now, task["job_id"], url_hash(url)) for url in load(task["urls"], [])],
    )
    if worker_id:
        await db.write(
            """UPDATE nodes SET inflight = MAX(0, inflight - 1),
                   completed_tasks = completed_tasks + 1 WHERE worker_id=?""",
            (worker_id,),
        )
    await db.write(
        "INSERT INTO task_events (task_id, job_id, worker_id, event, detail, created_at) VALUES (?, ?, ?, 'completed', '', ?)",
        (task_id, task["job_id"], worker_id or task["assigned_worker"], now),
    )
    await jobs.complete_if_done(db, hub, task["job_id"])
    await hub.broadcast(
        "task.completed",
        {"task_id": task_id, "job_id": task["job_id"], "worker_id": worker_id},
    )
    return await db.fetch_one("SELECT * FROM tasks WHERE task_id=?", (task_id,))


async def tick(db: Database, hub: EventHub) -> dict[str, int]:
    created = await decompose_once(db, hub)
    expired = await requeue_expired(db, hub)
    running = await db.fetch_all("SELECT job_id FROM jobs WHERE status='running'")
    completed = 0
    for row in running:
        if await jobs.complete_if_done(db, hub, row["job_id"]):
            completed += 1
    return {"decomposed": created, "expired": expired, "completed_jobs": completed}


async def job_task_summary(db: Database, job_id: str) -> list[dict]:
    return await db.fetch_all(
        """SELECT assigned_worker AS worker_id, status, COUNT(*) AS count
           FROM tasks WHERE job_id=? GROUP BY assigned_worker, status""",
        (job_id,),
    )


def lease_deadline(row: dict) -> datetime | None:
    return parse_dt(row.get("lease_deadline"))


def task_urls(row: dict) -> list[str]:
    return load(row.get("urls"), [])
