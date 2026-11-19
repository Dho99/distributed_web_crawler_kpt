from __future__ import annotations

import logging

from shared.models import (
    TaskFailRequest,
    TaskFailResponse,
    TaskResultRequest,
    TaskResultResponse,
    TaskStatus,
)
from shared.urlnorm import domain_of, normalize_url, url_hash

from ..db.database import Database, iso
from . import frontier, jobs, scheduler
from .hub import EventHub

log = logging.getLogger("crawlmesh.aggregator")


async def ingest_results(
    db: Database, hub: EventHub, task_id: str, payload: TaskResultRequest
) -> TaskResultResponse:
    task = await db.fetch_one("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
    if task is None:
        raise KeyError(task_id)

    already_finished = task["status"] == TaskStatus.COMPLETED.value
    job = await db.fetch_one("SELECT * FROM jobs WHERE job_id = ?", (task["job_id"],))
    if job is None:
        raise KeyError(task["job_id"])

    accepted = 0
    duplicates = 0
    failed = 0
    now = iso()

    for item in payload.results:
        url = normalize_url(item.final_url or item.url) or item.url
        digest = url_hash(url)
        rowcount = await db.write(
            """INSERT INTO results
               (task_id, job_id, url, url_hash, final_url, title, extracted_text, http_status,
                content_hash, response_time_ms, size_bytes, links_found, worker_id, crawled_at, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (job_id, url_hash) DO NOTHING""",
            (
                task_id,
                task["job_id"],
                url,
                digest,
                item.final_url or url,
                item.title[:500],
                item.extracted_text[:20_000],
                item.http_status,
                item.content_hash,
                item.response_time_ms,
                item.size_bytes,
                len(item.links),
                payload.worker_id,
                now,
                item.error,
            ),
        )
        if rowcount:
            accepted += 1
            if item.error:
                failed += 1
        else:
            duplicates += 1

    # Links discovered by the worker, plus links found inside each page.
    links: list[tuple[str, int]] = [(link.url, link.depth) for link in payload.links]
    next_depth = int(task["depth"]) + 1
    for item in payload.results:
        for link in item.links:
            links.append((link, next_depth))
    links_accepted = 0
    if links:
        links_accepted = await frontier.enqueue_urls(db, job, links)

    if not already_finished:
        await scheduler.finish_task(db, hub, task_id, payload.worker_id)

    summary = await db.fetch_one(
        "SELECT status FROM jobs WHERE job_id = ?", (task["job_id"],)
    )
    return TaskResultResponse(
        accepted=accepted,
        duplicates=duplicates,
        failed=failed,
        links_accepted=links_accepted,
        job_completed=bool(summary and summary["status"] == "completed"),
    )


async def fail_task(
    db: Database, hub: EventHub, task_id: str, payload: TaskFailRequest
) -> TaskFailResponse:
    task = await db.fetch_one("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
    if task is None:
        raise KeyError(task_id)
    if task["status"] in (TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value):
        return TaskFailResponse(requeued=False, attempt=int(task["attempt_count"] or 0))

    if payload.retriable:
        status = await scheduler._release_lease(db, task, payload.error or "worker reported failure")
        requeued = status == TaskStatus.QUEUED.value
    else:
        await db.write(
            "UPDATE tasks SET status='dead', failed_at=?, error=? WHERE task_id=?",
            (iso(), payload.error or "non-retriable failure", task_id),
        )
        if task["assigned_worker"]:
            await db.write(
                "UPDATE nodes SET inflight=MAX(0,inflight-1) WHERE worker_id=?",
                (task["assigned_worker"],),
            )
        requeued = False

    await hub.broadcast(
        "task.failed",
        {"task_id": task_id, "worker_id": payload.worker_id, "requeued": requeued},
    )
    job = await db.fetch_one("SELECT status FROM jobs WHERE job_id = ?", (task["job_id"],))
    if job and job["status"] == "running":
        await jobs.complete_if_done(db, hub, task["job_id"])

    updated = await db.fetch_one("SELECT attempt_count FROM tasks WHERE task_id=?", (task_id,))
    return TaskFailResponse(requeued=requeued, attempt=int((updated or {}).get("attempt_count") or 0))


async def task_stats(db: Database, job_id: str) -> dict:
    rows = await db.fetch_all(
        """SELECT status, COUNT(*) AS count FROM tasks WHERE job_id=? GROUP BY status""",
        (job_id,),
    )
    return {row["status"]: int(row["count"]) for row in rows}


async def domains_in_results(db: Database, job_id: str) -> list[str]:
    rows = await db.fetch_all(
        "SELECT DISTINCT url FROM results WHERE job_id=? LIMIT 500", (job_id,)
    )
    return sorted({domain_of(row["url"]) for row in rows if domain_of(row["url"])})
