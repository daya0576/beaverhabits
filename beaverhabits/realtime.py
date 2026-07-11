import datetime
from collections import defaultdict

from fastapi import WebSocket

from beaverhabits.storage.storage import CheckedRecord, Habit


class ConnectionManager:
    def __init__(self) -> None:
        self._conns: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._conns[user_id].add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        self._conns[user_id].discard(websocket)
        if not self._conns[user_id]:
            self._conns.pop(user_id, None)

    async def broadcast(
        self,
        user_id: str,
        message: dict,
        *,
        exclude: WebSocket | None = None,
    ) -> None:
        for connection in list(self._conns.get(user_id, ())):
            if connection is exclude:
                continue
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(user_id, connection)


manager = ConnectionManager()


async def apply_tick(
    habit: Habit,
    day: datetime.date,
    done: bool,
    text: str | None = None,
    *,
    user_id: str | None = None,
    exclude: WebSocket | None = None,
) -> CheckedRecord:
    """Persist one tick and broadcast the authoritative value to native clients."""
    record = await habit.tick(day, done, text)
    resolved_user_id = user_id or getattr(habit.habit_list, "sync_user_id", None)
    if resolved_user_id:
        await manager.broadcast(
            resolved_user_id,
            {
                "type": "tick",
                "habit_id": habit.id,
                "day": day.strftime("%Y-%m-%d"),
                "done": record.done,
                "text": record.text or None,
            },
            exclude=exclude,
        )
    return record
