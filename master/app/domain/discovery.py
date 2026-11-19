from __future__ import annotations

import asyncio
import json
import logging
import socket
import time

from shared.models import DiscoveredNode
from shared.netinfo import disable_udp_connreset

log = logging.getLogger("crawlmesh.discovery")

DISCOVERY_KIND = "crawlmesh.discover"
ANNOUNCE_KIND = "crawlmesh.agent"


def _scan_sync(port: int, cluster_id: str | None, window_ms: int) -> list[dict]:
    """Broadcast a probe and collect agent replies on the *same* socket.

    Replies must come back to the probing socket's ephemeral port, so the
    probe cannot be sent from a separate socket.
    """
    payload = json.dumps({"kind": DISCOVERY_KIND, "cluster_id": cluster_id, "v": 1}).encode()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    found: dict[str, dict] = {}
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        disable_udp_connreset(sock)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        except OSError:
            pass
        sock.bind(("", 0))
        sock.settimeout(0.2)

        for _ in range(2):
            for target in ("255.255.255.255", "127.0.0.1"):
                try:
                    sock.sendto(payload, (target, port))
                except OSError:
                    continue
            time.sleep(0.05)

        deadline = time.monotonic() + (window_ms / 1000.0)
        while time.monotonic() < deadline:
            try:
                data, addr = sock.recvfrom(8192)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                info = json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if info.get("kind") != ANNOUNCE_KIND:
                continue
            worker_id = str(info.get("worker_id") or "")
            if not worker_id:
                continue
            info["ip_address"] = addr[0]
            found[worker_id] = info
    finally:
        sock.close()
    return list(found.values())


async def scan_network(port: int, cluster_id: str | None, window_ms: int) -> list[DiscoveredNode]:
    loop = asyncio.get_running_loop()
    raw = await loop.run_in_executor(None, _scan_sync, port, cluster_id, window_ms)
    nodes: list[DiscoveredNode] = []
    for item in raw:
        try:
            nodes.append(
                DiscoveredNode(
                    worker_id=item["worker_id"],
                    hostname=item.get("hostname", "unknown"),
                    ip_address=item.get("ip_address", ""),
                    port=int(item.get("port", 8010)),
                    cpu_cores=int(item.get("cpu_cores", 1)),
                    memory_total=int(item.get("memory_total", 0)),
                    os_name=item.get("os_name", ""),
                    python_version=item.get("python_version", ""),
                    agent_version=item.get("agent_version", ""),
                    cluster_id=item.get("cluster_id"),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return nodes
