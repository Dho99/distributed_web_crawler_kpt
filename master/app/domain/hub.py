from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

log = logging.getLogger("crawlmesh.hub")


class EventHub:
    """Fan-out of real-time events to GUI WebSocket clients.

    Slow clients are dropped rather than allowed to block the orchestrator.
    """

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def broadcast(self, kind: str, payload: Any) -> None:
        if not self._clients:
            return
        message = {
            "kind": kind,
            "ts": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        async with self._lock:
            clients = list(self._clients)

        dead: list[WebSocket] = []
        for ws in clients:
            try:
                await asyncio.wait_for(ws.send_json(message), timeout=1.5)
            except Exception:  # noqa: BLE001 - any failure means drop the client
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.discard(ws)
                    with contextlib.suppress(Exception):
                        await ws.close()
