from __future__ import annotations

import random
from functools import lru_cache

from fastapi import APIRouter, Response

router = APIRouter(prefix="/bench", tags=["bench"], include_in_schema=False)

PAGE_COUNT = 300
PAGE_BYTES = 120_000
LINKS_PER_PAGE = 32

WORDS = (
    "crawl mesh distributed worker master scheduler frontier throughput latency "
    "parallel process pool lease heartbeat requeue benchmark cluster node parsing "
    "extraction content hash queue batch depth domain scope robots token"
).split()


def _filler(seed: int, size: int) -> str:
    rng = random.Random(seed)
    chunks: list[str] = []
    total = 0
    while total < size:
        sentence = " ".join(rng.choice(WORDS) for _ in range(12)).capitalize() + "."
        chunks.append(sentence)
        total += len(sentence) + 1
    return " ".join(chunks)


def _links(n: int) -> list[int]:
    rng = random.Random(1000 + n)
    targets = [target for target in range(1, PAGE_COUNT + 1) if target != n]
    return rng.sample(targets, k=min(LINKS_PER_PAGE, len(targets)))


@lru_cache(maxsize=512)
def render_page(n: int) -> str:
    body = _filler(n, PAGE_BYTES)
    links = "\n".join(
        f'<li><a href="/bench/{target}.html">Bench page {target}</a></li>' for target in _links(n)
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Bench Page {n:03d} — CrawlMesh</title>
<meta name="description" content="Deterministic benchmark page {n} for CrawlMesh">
</head>
<body>
<h1>Bench Page {n:03d}</h1>
<p id="lead">Deterministic page generated for reproducible crawl benchmarks.</p>
<ul>
{links}
</ul>
<article>
<p>{body}</p>
</article>
<footer>page {n} of {PAGE_COUNT}</footer>
</body>
</html>"""


@lru_cache(maxsize=1)
def render_index() -> str:
    links = "\n".join(
        f'<li><a href="/bench/{n}.html">Bench Page {n:03d}</a></li>' for n in range(1, 41)
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CrawlMesh Bench Site</title>
<meta name="description" content="Static benchmark site served by the CrawlMesh master">
</head>
<body>
<h1>CrawlMesh Bench Site</h1>
<p>{PAGE_COUNT} static pages, {PAGE_BYTES // 1000} KB each, deterministic link graph.</p>
<ul>
{links}
</ul>
</body>
</html>"""


@router.get("/robots.txt", include_in_schema=False)
async def robots() -> Response:
    return Response("User-agent: *\nAllow: /\n", media_type="text/plain")


@router.get("/_warm", include_in_schema=False)
async def warm() -> Response:
    """Render every bench page once so crawl timing measures crawling, not generation."""
    for n in range(1, PAGE_COUNT + 1):
        render_page(n)
    render_index()
    return Response(f"warmed {PAGE_COUNT}", media_type="text/plain")


@router.get("/")
async def index() -> Response:
    return Response(render_index(), media_type="text/html; charset=utf-8")


@router.get("")
async def index_bare() -> Response:
    return await index()


@router.get("/{n}.html")
async def page(n: int) -> Response:
    if n < 1 or n > PAGE_COUNT:
        return Response("not found", status_code=404, media_type="text/plain")
    return Response(render_page(n), media_type="text/html; charset=utf-8")


@router.get("/{n}")
async def page_bare(n: int) -> Response:
    return await page(n)
