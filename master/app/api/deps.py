from __future__ import annotations

import secrets

from fastapi import HTTPException, Request

from ..core.config import Settings, get_settings
from ..db.database import Database
from ..domain.hub import EventHub


def get_db(request: Request) -> Database:
    return request.app.state.db


def get_hub(request: Request) -> EventHub:
    return request.app.state.hub


def get_settings_dep() -> Settings:
    return get_settings()


async def require_token(request: Request, db: Database) -> None:
    """Worker endpoints are authenticated with the cluster pairing token."""
    row = await db.fetch_one("SELECT pairing_token FROM cluster WHERE id = 1")
    if row is None:
        raise HTTPException(status_code=409, detail="Master belum diinisialisasi")
    header = request.headers.get("X-Cluster-Token", "")
    if not secrets.compare_digest(header, row["pairing_token"]):
        raise HTTPException(status_code=401, detail="Pairing token tidak valid")
