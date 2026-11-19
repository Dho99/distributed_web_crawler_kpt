from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..domain import cluster as cluster_service

router = APIRouter(tags=["realtime"])


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    db = ws.app.state.db
    hub = ws.app.state.hub
    await hub.connect(ws)
    try:
        snapshot = await cluster_service.overview(db)
        await ws.send_json(
            {
                "kind": "snapshot",
                "ts": datetime.now(timezone.utc).isoformat(),
                "payload": snapshot.model_dump(mode="json"),
            }
        )
        while True:
            message = await ws.receive_text()
            if message == "ping":
                await ws.send_json(
                    {
                        "kind": "pong",
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "payload": {"clients": hub.client_count},
                    }
                )
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001 - a broken socket must not crash the loop
        pass
    finally:
        await hub.disconnect(ws)
