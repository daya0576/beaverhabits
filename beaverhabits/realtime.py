from collections import defaultdict

from fastapi import WebSocket

from beaverhabits.events import TickChanged, subscribe
from beaverhabits.logger import logger


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

    async def broadcast(self, event: TickChanged) -> None:
        message = {
            "type": "tick_changed",
            "habit_id": event.habit_id,
            "day": event.day.strftime("%Y-%m-%d"),
            "done": event.done,
            "text": event.text,
            "timestamp": event.timestamp,
        }
        for connection in list(self._connections.get(event.user_id, ())):
            try:
                await connection.send_json(message)
            except Exception as error:
                logger.warning(
                    f"[ws] broadcast failed user={event.user_id} "
                    f"habit={event.habit_id} day={message['day']} error={error}"
                )
                self.disconnect(event.user_id, connection)
            else:
                logger.info(
                    f"[ws] broadcast tick_changed user={event.user_id} "
                    f"habit={event.habit_id} day={message['day']}"
                )


manager = ConnectionManager()


@subscribe(TickChanged)
async def broadcast_tick_changed(event: TickChanged) -> None:
    await manager.broadcast(event)
