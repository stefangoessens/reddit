"""FastAPI application setup."""
from __future__ import annotations

from contextlib import asynccontextmanager
from functools import lru_cache
from typing import AsyncIterator

from fastapi import Depends, FastAPI

from api.router import router
from api.service import TrendService
from api.stream import broadcaster
from common.config import get_settings
from common.db import PostgresClient
from price.client import PolygonClient
from price.service import MinuteBarRepository, PriceService


@lru_cache
def get_db() -> PostgresClient:
    settings = get_settings()
    return PostgresClient(dsn=str(settings.postgres.dsn))


@lru_cache
def get_price_service() -> PriceService:
    settings = get_settings()
    provider = PolygonClient(settings.price_feed)
    repo = MinuteBarRepository(get_db())
    return PriceService(provider, repo)


async def get_trend_service(db: PostgresClient = Depends(get_db)) -> TrendService:
    return TrendService(db)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db = get_db()
    await db.connect()
    try:
        yield
    finally:
        await db.close()


app = FastAPI(title="WSB Hype Radar", lifespan=lifespan)
app.include_router(router, dependencies=[Depends(get_trend_service)])
