from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import aiosqlite

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None = None) -> str:
    return (dt or utcnow()).isoformat()


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def dump(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), default=str)


def load(value: str | None, default: Any = None) -> Any:
    if not value:
        return default if default is not None else {}
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default if default is not None else {}


class Database:
    """Thin async SQLite wrapper: one connection, serialized writes."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None
        self._write_lock = asyncio.Lock()

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(self.path)
        conn.row_factory = aiosqlite.Row
        self._conn = conn
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute("PRAGMA busy_timeout=5000")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        await conn.commit()
        await self._migrate()

    async def _migrate(self) -> None:
        """Additive migrations for databases created by older builds."""
        expected = {
            "nodes": {"simulated_offline": "INTEGER NOT NULL DEFAULT 0"},
            "jobs": {
                "include_subdomains": "INTEGER NOT NULL DEFAULT 0",
                "allow_private_targets": "INTEGER NOT NULL DEFAULT 0",
                "worker_allowlist": "TEXT NOT NULL DEFAULT '[]'",
            },
            "experiments": {
                "status": "TEXT NOT NULL DEFAULT 'completed'",
                "group_id": "TEXT",
                "progress_pages": "INTEGER NOT NULL DEFAULT 0",
                "total_pages": "INTEGER NOT NULL DEFAULT 0",
                "error": "TEXT",
                "finished_at": "TEXT",
            },
        }
        for table, columns in expected.items():
            cur = await self.conn.execute(f"PRAGMA table_info({table})")
            existing = {row[1] for row in await cur.fetchall()}
            await cur.close()
            for name, ddl in columns.items():
                if name not in existing:
                    await self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
        await self.conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("database not connected")
        return self._conn

    async def write(self, sql: str, params: Sequence[Any] = ()) -> int:
        async with self._write_lock:
            cur = await self.conn.execute(sql, params)
            await self.conn.commit()
            return cur.rowcount

    async def insert(self, sql: str, params: Sequence[Any] = ()) -> int:
        async with self._write_lock:
            cur = await self.conn.execute(sql, params)
            await self.conn.commit()
            return int(cur.lastrowid or 0)

    async def write_many(self, sql: str, rows: Iterable[Sequence[Any]]) -> int:
        async with self._write_lock:
            cur = await self.conn.executemany(sql, list(rows))
            await self.conn.commit()
            return cur.rowcount

    async def fetch_all(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        cur = await self.conn.execute(sql, params)
        rows = await cur.fetchall()
        await cur.close()
        return [dict(row) for row in rows]

    async def fetch_one(self, sql: str, params: Sequence[Any] = ()) -> dict[str, Any] | None:
        cur = await self.conn.execute(sql, params)
        row = await cur.fetchone()
        await cur.close()
        return dict(row) if row else None

    async def scalar(self, sql: str, params: Sequence[Any] = (), default: Any = 0) -> Any:
        row = await self.fetch_one(sql, params)
        if not row:
            return default
        value = next(iter(row.values()))
        return default if value is None else value
