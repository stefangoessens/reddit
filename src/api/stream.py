"""Server-sent events helper for alert streaming."""
from __future__ import annotations

import asyncio
from collections import deque
from typing import AsyncIterator, Deque

from common.models import AlertEvent


class AlertBroadcaster:
    """In-memory fan-out for alerts (backed by asyncio queues)."""

    def __init__(self, max_history: int = 100) -> None:
        self._subscribers: Deque[asyncio.Queue[AlertEvent]] = deque()
        self._history: Deque[AlertEvent] = deque(maxlen=max_history)

    async def publish(self, alert: AlertEvent) -> None:
        self._history.append(alert)
        for queue in list(self._subscribers):
            await queue.put(alert)

    async def subscribe(self) -> AsyncIterator[AlertEvent]:
        queue: asyncio.Queue[AlertEvent] = asyncio.Queue()
        self._subscribers.append(queue)
        try:
            for alert in self._history:
                await queue.put(alert)
            while True:
                yield await queue.get()
        finally:
            self._subscribers.remove(queue)


broadcaster = AlertBroadcaster()
