from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CRAWLMESH_", env_file=".env", extra="ignore")

    app_name: str = "CrawlMesh"
    host: str = "0.0.0.0"
    port: int = 8000
    discovery_port: int = 5599
    data_dir: Path = REPO_ROOT / "data"
    static_dir: Path = Path(__file__).resolve().parents[1] / "static"

    heartbeat_interval: int = 5
    offline_threshold: int = 15
    metrics_sample_ms: int = 2000
    discovery_window_ms: int = 2500
    task_retry_limit: int = 3
    lease_grace_seconds: int = 60

    # Benchmark mode knobs (Phase 6)
    sequential_max_pages: int = Field(default=50, ge=1)

    # Crawler safety
    allow_private_targets: bool = False
    default_user_agent: str = "CrawlMesh/0.1 (+academic-project)"

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def db_path(self) -> Path:
        return self.data_dir / "crawlmesh.db"

    @property
    def master_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
