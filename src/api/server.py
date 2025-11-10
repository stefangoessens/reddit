"""FastAPI gateway with trending + alert streaming endpoints."""
from __future__ import annotations

from contextlib import asynccontextmanager
from functools import lru_cache
from typing import AsyncIterator

from fastapi import Depends, FastAPI, Query
from fastapi.responses import StreamingResponse

from api.service import TrendService
from api.stream import broadcaster
from common.config import get_settings
from common.db import PostgresClient


@lru_cache
def get_db() -> PostgresClient:
    settings = get_settings()
    return PostgresClient(dsn=str(settings.postgres.dsn))


def get_trend_service(db: PostgresClient = Depends(get_db)) -> TrendService:
    return TrendService(db)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db = get_db()
    await db.connect()
    try:
        yield
    finally:
        await db.close()


app = FastAPI(title="WSB Hype Radar", docs_url=None, redoc_url=None, lifespan=lifespan)


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/trending")
async def trending(
    window: str = Query(default="5m"),
    limit: int = Query(default=10, le=100),
    svc: TrendService = Depends(get_trend_service),
) -> list[dict]:
    return await svc.top_trending(window=window, limit=limit)


@app.get("/v1/alerts/live")
async def alerts_live() -> StreamingResponse:
    async def event_stream():
        async for alert in broadcaster.subscribe():
            yield f"data: {alert.model_dump_json()}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
