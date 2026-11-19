from __future__ import annotations

import os
import socket
import uuid
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CRAWLMESH_", env_file=".env", extra="ignore")

    master_url: str = "http://127.0.0.1:8000"
    token: str = ""
    worker_name: str = ""
    port: int = 8010
    discovery_port: int = 5599
    pool_size: int = Field(default=0, ge=0)
    capacity: int = Field(default=0, ge=0)
    fetch_concurrency: int = 4
    state_dir: Path = Path(".crawlmesh-agent")
    heartbeat_interval: int = 5
    lease_interval: float = 0.25
    agent_version: str = "0.1.0"

    def resolved_pool_size(self) -> int:
        if self.pool_size > 0:
            return self.pool_size
        return max(1, (os.cpu_count() or 2) - 1)

    def resolved_capacity(self) -> int:
        return self.capacity if self.capacity > 0 else self.resolved_pool_size()

    @property
    def hostname(self) -> str:
        return self.worker_name or socket.gethostname()

    def worker_id(self) -> str:
        """Stable identity across restarts on the same machine."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        path = self.state_dir / "worker-id"
        if path.exists():
            value = path.read_text(encoding="utf-8").strip()
            if value:
                return value
        slug = "".join(ch if ch.isalnum() else "-" for ch in self.hostname.lower())[:24]
        value = f"worker-{slug}-{uuid.uuid4().hex[:6]}"
        path.write_text(value, encoding="utf-8")
        return value

    def local_ip(self) -> str:
        from shared.netinfo import local_ip

        return local_ip()
