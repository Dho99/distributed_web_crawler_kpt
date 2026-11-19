from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from shared.urlnorm import domain_of, in_scope, is_safe_public_url, normalize_url, url_hash

from ..db.database import Database, iso, load

log = logging.getLogger("crawlmesh.frontier")

MAX_URLS_PER_BATCH = 500
_enqueue_lock = asyncio.Lock()


def seed_domains(job: dict) -> list[str]:
    domains = load(job.get("allowed_domains"), [])
    if domains:
        return domains
    return sorted({domain_of(url) for url in load(job.get("seed_urls"), []) if domain_of(url)})


def page_budget_left(job: dict, used: int) -> int:
    return max(0, int(job["maximum_pages"]) - used)


async def enqueue_urls(
    db: Database,
    job: dict,
    links: Iterable[tuple[str, int]],
    priority: int = 0,
) -> int:
    """Normalize, scope-check, dedupe and budget-check then persist to the frontier."""
    job_id = job["job_id"]
    allowed = seed_domains(job)
    include_subdomains = bool(job.get("include_subdomains", 0))
    allow_private = bool(job.get("allow_private_targets", 0))
    max_depth = int(job["maximum_depth"])

    async with _enqueue_lock:
        used = await db.scalar("SELECT COUNT(*) FROM frontier_urls WHERE job_id = ?", (job_id,))
        budget = page_budget_left(job, int(used))
        if budget <= 0:
            return 0

        now = iso()
        rows: list[tuple] = []
        seen: set[str] = set()
        for raw_url, depth in links:
            if len(rows) >= budget:
                break
            if depth > max_depth:
                continue
            url = normalize_url(raw_url)
            if url is None:
                continue
            if not in_scope(url, allowed, include_subdomains):
                continue
            if not allow_private and not is_safe_public_url(url):
                continue
            digest = url_hash(url)
            if digest in seen:
                continue
            seen.add(digest)
            rows.append((job_id, url, digest, domain_of(url), depth, priority, now))

        if not rows:
            return 0
        return await db.write_many(
            """INSERT INTO frontier_urls
               (job_id, url, url_hash, domain, depth, priority, state, discovered_at)
               VALUES (?, ?, ?, ?, ?, ?, 'queued', ?)
               ON CONFLICT (job_id, url_hash) DO NOTHING""",
            rows,
        )


async def backlog(db: Database, job_id: str) -> dict[str, int]:
    row = await db.fetch_one(
        """SELECT
             SUM(CASE WHEN state = 'queued' THEN 1 ELSE 0 END) AS queued,
             SUM(CASE WHEN state = 'scheduled' THEN 1 ELSE 0 END) AS scheduled,
             COUNT(*) AS total
           FROM frontier_urls WHERE job_id = ?""",
        (job_id,),
    )
    return {
        "queued": int(row["queued"] or 0) if row else 0,
        "scheduled": int(row["scheduled"] or 0) if row else 0,
        "total": int(row["total"] or 0) if row else 0,
    }
