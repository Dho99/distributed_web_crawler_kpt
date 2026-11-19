from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core.config import Settings, get_settings
from ..db.database import Database
from ..domain import cluster as cluster_service
from .deps import get_db

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
async def health(db: Database = Depends(get_db), settings: Settings = Depends(get_settings)):
    cluster = await cluster_service.get_cluster(db)
    return {
        "status": "ok",
        "service": "crawlmesh-master",
        "version": "0.1.0",
        "cluster_id": cluster.cluster_id if cluster else None,
        "initialized": cluster is not None,
        "db": str(settings.db_path),
    }
