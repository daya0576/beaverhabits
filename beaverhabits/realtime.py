import asyncio
import datetime
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Awaitable, Callable

from fastapi import WebSocket

from beaverhabits.storage.storage import Habit


@dataclass(frozen=True)
class TickChanged:
    user_id: str
    habit_id: str
    day: datetime.date
    done: bool
    text: str | None
    timestamp: int


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        self._connections[user_id].discard(websocket)
        if not self._connections[user_id]:
            self._connections.pop(user_id, None)

    async def broadcast(
        self,
        event: TickChanged,
        exclude: WebSocket | None,
    ) -> None:
        message = {
            "type": "tick_changed",
            "habit_id": event.habit_id,
            "day": event.day.strftime("%Y-%m-%d"),
            "done": event.done,
            "text": event.text,
            "timestamp": event.timestamp,
        }
        for connection in list(self._connections.get(event.user_id, ())):
            if connection is exclude:
                continue
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(event.user_id, connection)


manager = ConnectionManager()
TickChangedHandler = Callable[[TickChanged, WebSocket | None], Awaitable[None]]
_tick_changed_handlers: list[TickChangedHandler] = [manager.broadcast]
_background_tasks: set[asyncio.Task] = set()


def emit_tick_changed(event: TickChanged, exclude: WebSocket | None = None) -> None:
    for handler in _tick_changed_handlers:
        task = asyncio.create_task(handler(event, exclude))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)


async def apply_tick(
    habit: Habit,
    day: datetime.date,
    done: bool,
    text: str | None = None,
    *,
    user_id: str | None = None,
    exclude: WebSocket | None = None,
) -> TickChanged:
    record = await habit.tick(day, done, text)
    timestamp = time.time_ns() // 1_000_000
    record_data = getattr(record, "data", None)
    if isinstance(record_data, dict):
        record_data["timestamp"] = timestamp

    event = TickChanged(
        user_id=user_id or getattr(habit.habit_list, "sync_user_id", ""),
        habit_id=habit.id,
        day=day,
        done=record.done,
        text=record.text or None,
        timestamp=timestamp,
    )
    if event.user_id:
        emit_tick_changed(event, exclude)
    return event
