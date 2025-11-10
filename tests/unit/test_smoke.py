import pytest

from api.server import healthcheck


@pytest.mark.asyncio
async def test_healthcheck_returns_ok() -> None:
    assert (await healthcheck())["status"] == "ok"
