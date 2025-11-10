"""Async Postgres client helper built on asyncpg."""
from __future__ import annotations

import asyncio
from typing import Any, Iterable, Sequence

import asyncpg


class PostgresClient:
    """Lightweight asyncpg wrapper with pooled connections."""

    def __init__(self, dsn: str, min_size: int = 1, max_size: int = 10) -> None:
        self._dsn = dsn
        self._min_size = min_size
        self._max_size = max_size
        self._pool: asyncpg.Pool | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if self._pool:
            return
        async with self._lock:
            if self._pool is None:
                self._pool = await asyncpg.create_pool(
                    dsn=self._dsn,
                    min_size=self._min_size,
                    max_size=self._max_size,
                )

    async def close(self) -> None:
        if not self._pool:
            return
        async with self._lock:
            if self._pool is not None:
                await self._pool.close()
                self._pool = None

    async def execute(self, query: str, *args: Any) -> str:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def executemany(self, query: str, args: Iterable[Sequence[Any]]) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.executemany(query, args)

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
        return list(rows)

    async def _ensure_pool(self) -> asyncpg.Pool:
        if not self._pool:
            await self.connect()
        assert self._pool is not None
        return self._pool
