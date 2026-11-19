from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
import time
import urllib.robotparser
from urllib.parse import urlsplit

import httpx

log = logging.getLogger("crawlmesh.agent.crawler")

MAX_BYTES = 3_000_000
HTML_TYPES = ("text/html", "application/xhtml+xml")


async def _host_is_private(host: str) -> bool:
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(host, None)
    except (socket.gaierror, OSError):
        return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            return True
    return False


class CrawlFetcher:
    def __init__(self, user_agent: str, concurrency: int = 4) -> None:
        self.user_agent = user_agent
        self._client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(20.0, connect=8.0),
            headers={"User-Agent": user_agent, "Accept": "text/html,*/*;q=0.8"},
            limits=httpx.Limits(max_connections=concurrency * 2, max_keepalive_connections=concurrency),
        )
        self._robots: dict[str, tuple[float, urllib.robotparser.RobotFileParser | None]] = {}
        self._domain_gate: dict[str, float] = {}
        self._gate_lock = asyncio.Lock()

    async def close(self) -> None:
        await self._client.aclose()

    async def _wait_turn(self, host: str, delay: float) -> None:
        if delay <= 0:
            return
        async with self._gate_lock:
            now = time.monotonic()
            next_allowed = self._domain_gate.get(host, 0.0)
            wait = max(0.0, next_allowed - now)
            self._domain_gate[host] = max(now, next_allowed) + delay
        if wait:
            await asyncio.sleep(wait)

    async def _robots_allowed(self, url: str, respect: bool) -> bool:
        if not respect:
            return True
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        cached = self._robots.get(origin)
        now = time.monotonic()
        if cached and now - cached[0] < 3600:
            parser = cached[1]
        else:
            parser = None
            try:
                response = await self._client.get(f"{origin}/robots.txt", timeout=5.0)
                if response.status_code == 200 and len(response.text) < 200_000:
                    parser = urllib.robotparser.RobotFileParser()
                    parser.parse(response.text.splitlines())
            except httpx.HTTPError:
                parser = None
            self._robots[origin] = (now, parser)
        if parser is None:
            return True
        return parser.can_fetch(self.user_agent, url)

    async def fetch(
        self,
        url: str,
        timeout: float,
        respect_robots: bool,
        domain_delay: float,
        allow_private: bool,
    ) -> dict:
        host = (urlsplit(url).hostname or "").lower()
        result: dict = {
            "url": url,
            "final_url": url,
            "http_status": 0,
            "html": "",
            "size_bytes": 0,
            "content_type": "",
            "response_time_ms": 0.0,
            "error": None,
        }

        if not host:
            result["error"] = "invalid host"
            return result

        if not allow_private and await _host_is_private(host):
            result["error"] = "blocked private address"
            return result

        if not await self._robots_allowed(url, respect_robots):
            result["error"] = "disallowed by robots.txt"
            return result

        await self._wait_turn(host, domain_delay)
        started = time.perf_counter()
        try:
            response = await self._client.get(url, timeout=timeout)
        except httpx.HTTPError as exc:
            result["response_time_ms"] = round((time.perf_counter() - started) * 1000, 2)
            result["error"] = f"{type(exc).__name__}: {exc}"
            return result

        elapsed = round((time.perf_counter() - started) * 1000, 2)
        result["response_time_ms"] = elapsed
        result["http_status"] = response.status_code
        result["final_url"] = str(response.url)
        result["size_bytes"] = len(response.content)
        result["content_type"] = response.headers.get("content-type", "")

        if response.status_code >= 400:
            result["error"] = f"HTTP {response.status_code}"
            return result
        if len(response.content) > MAX_BYTES:
            result["error"] = "response too large"
            return result
        if not any(kind in result["content_type"] for kind in HTML_TYPES):
            result["error"] = f"unsupported content-type: {result['content_type'] or 'unknown'}"
            return result

        result["html"] = response.text
        return result
