from __future__ import annotations

import csv
import io
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from shared.models import CrawlJobConfig, CrawlJobOut, JobStatus

from ..db.database import Database
from ..domain import jobs as job_service
from ..domain.hub import EventHub
from .deps import get_db, get_hub

router = APIRouter(prefix="/api", tags=["crawl"])


@router.post("/jobs", response_model=CrawlJobOut, status_code=201)
async def create_job(
    config: CrawlJobConfig,
    db: Database = Depends(get_db),
    hub: EventHub = Depends(get_hub),
) -> CrawlJobOut:
    try:
        return await job_service.create_job(db, hub, config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/jobs", response_model=list[CrawlJobOut])
async def list_jobs(
    include_experiments: bool = False, db: Database = Depends(get_db)
) -> list[CrawlJobOut]:
    return await job_service.list_jobs(db, include_experiments=include_experiments)


@router.get("/jobs/{job_id}", response_model=CrawlJobOut)
async def get_job(job_id: str, db: Database = Depends(get_db)) -> CrawlJobOut:
    job = await job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan")
    return job


async def _transition(
    job_id: str, status: JobStatus, db: Database, hub: EventHub
) -> CrawlJobOut:
    job = await job_service.set_status(db, hub, job_id, status)
    if job is None:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan")
    return job


@router.post("/jobs/{job_id}/pause", response_model=CrawlJobOut)
async def pause_job(job_id: str, db: Database = Depends(get_db), hub: EventHub = Depends(get_hub)):
    return await _transition(job_id, JobStatus.PAUSED, db, hub)


@router.post("/jobs/{job_id}/resume", response_model=CrawlJobOut)
async def resume_job(job_id: str, db: Database = Depends(get_db), hub: EventHub = Depends(get_hub)):
    return await _transition(job_id, JobStatus.RUNNING, db, hub)


@router.post("/jobs/{job_id}/cancel", response_model=CrawlJobOut)
async def cancel_job(job_id: str, db: Database = Depends(get_db), hub: EventHub = Depends(get_hub)):
    return await _transition(job_id, JobStatus.CANCELLED, db, hub)


@router.get("/tasks")
async def list_tasks(
    job_id: str | None = None,
    status: str | None = None,
    worker: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Database = Depends(get_db),
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if job_id:
        clauses.append("job_id = ?")
        params.append(job_id)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if worker:
        clauses.append("assigned_worker = ?")
        params.append(worker)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    rows = await db.fetch_all(
        f"""SELECT task_id, job_id, depth, url_count, assigned_worker, attempt_count,
                   status, created_at, leased_at, completed_at, error
            FROM tasks {where} ORDER BY created_at DESC LIMIT ?""",
        params,
    )
    return rows


@router.get("/results")
async def list_results(
    job_id: str | None = None,
    q: str | None = None,
    status: int | None = None,
    worker: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    clauses: list[str] = []
    params: list[Any] = []
    if job_id:
        clauses.append("job_id = ?")
        params.append(job_id)
    if q:
        clauses.append("(url LIKE ? OR title LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    if status is not None:
        clauses.append("http_status = ?")
        params.append(status)
    if worker:
        clauses.append("worker_id = ?")
        params.append(worker)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    total = await db.scalar(f"SELECT COUNT(*) FROM results {where}", params)
    rows = await db.fetch_all(
        f"""SELECT result_id, job_id, url, title, http_status, response_time_ms,
                   links_found, size_bytes, content_hash, worker_id, crawled_at, error
            FROM results {where}
            ORDER BY result_id DESC LIMIT ? OFFSET ?""",
        [*params, limit, offset],
    )
    return {"total": int(total or 0), "items": rows}


@router.get("/results/export")
async def export_results(
    job_id: str | None = None,
    format: Literal["csv", "json"] = "csv",
    db: Database = Depends(get_db),
) -> Response:
    params: list[Any] = []
    where = ""
    if job_id:
        where = "WHERE job_id = ?"
        params.append(job_id)
    rows = await db.fetch_all(
        f"""SELECT url, final_url, http_status, title, links_found, content_hash,
                   response_time_ms, size_bytes, worker_id, crawled_at, error
            FROM results {where} ORDER BY result_id ASC""",
        params,
    )
    if format == "json":
        return Response(
            _json_dumps(rows), media_type="application/json", headers=_download_headers("json")
        )
    return Response(
        _to_csv(rows), media_type="text/csv", headers=_download_headers("csv")
    )


@router.get("/metrics/timeseries")
async def metrics_timeseries(
    minutes: int = Query(default=10, ge=1, le=180),
    db: Database = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = await db.fetch_all(
        """SELECT worker_id, cpu_usage, memory_usage, throughput, active_tasks, recorded_at
           FROM worker_metrics
           WHERE recorded_at >= datetime('now', ?)
           ORDER BY recorded_at ASC""",
        (f"-{minutes} minutes",),
    )
    return rows


@router.get("/jobs/{job_id}/frontier")
async def job_frontier(job_id: str, db: Database = Depends(get_db)) -> dict[str, Any]:
    rows = await db.fetch_all(
        """SELECT state, COUNT(*) AS count FROM frontier_urls WHERE job_id=? GROUP BY state""",
        (job_id,),
    )
    return {row["state"]: int(row["count"]) for row in rows}


def _to_csv(rows: list[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    if not rows:
        buffer.write("url,http_status,title,links_found,response_time_ms,worker_id,crawled_at\n")
        return buffer.getvalue()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _json_dumps(rows: list[dict[str, Any]]) -> str:
    import json

    return json.dumps(rows, indent=2, default=str)


def _download_headers(extension: str) -> dict[str, str]:
    return {"Content-Disposition": f'attachment; filename="crawlmesh-results.{extension}"'}
