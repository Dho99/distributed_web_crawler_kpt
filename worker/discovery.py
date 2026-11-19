from __future__ import annotations

import asyncio
import json
import logging
import socket
from typing import Any

from shared.netinfo import disable_udp_connreset

log = logging.getLogger("crawlmesh.agent.discovery")


class _DiscoveryProtocol(asyncio.DatagramProtocol):
    def __init__(self, info_provider) -> None:
        self._info = info_provider
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]

    def connection_lost(self, exc: Exception | None) -> None:
        if exc is not None:
            log.warning("discovery transport lost: %s", exc)
        self.transport = None

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            payload = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        if payload.get("kind") != "crawlmesh.discover":
            return
        try:
            reply = self._info()
            reply["kind"] = "crawlmesh.agent"
            reply["v"] = 1
            blob = json.dumps(reply).encode("utf-8")
        except Exception:  # noqa: BLE001
            log.exception("discovery reply build failed")
            return
        if self.transport is not None:
            self.transport.sendto(blob, addr)
            log.debug("discovery reply sent to %s", addr)

    def error_received(self, exc: Exception) -> None:
        log.debug("discovery socket error: %s", exc)


async def start_listener(port: int, info_provider) -> tuple[asyncio.DatagramTransport, Any]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    disable_udp_connreset(sock)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    except OSError:
        pass
    sock.bind(("", port))
    sock.setblocking(False)
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: _DiscoveryProtocol(info_provider), sock=sock
    )
    log.info("discovery listener on udp/%s", port)
    return transport, protocol
