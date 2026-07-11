import datetime

from beaverhabits.events import TickChanged
from beaverhabits.logger import logger
from beaverhabits.realtime import ConnectionManager


class FakeWebSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.messages: list[dict] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.messages.append(message)


async def test_broadcast_logs_each_successful_websocket_push() -> None:
    manager = ConnectionManager()
    first = FakeWebSocket()
    second = FakeWebSocket()
    await manager.connect("user-1", first)  # type: ignore[arg-type]
    await manager.connect("user-1", second)  # type: ignore[arg-type]

    logs: list[str] = []
    sink = logger.add(logs.append, format="{message}")
    try:
        await manager.broadcast(
            TickChanged(
                user_id="user-1",
                habit_id="habit-1",
                day=datetime.date(2026, 7, 11),
                done=True,
                text=None,
                timestamp=1_783_728_000_000,
            )
        )
    finally:
        logger.remove(sink)

    assert first.messages == second.messages
    assert first.messages[0]["type"] == "tick_changed"
    matching_logs = [line for line in logs if "[ws] broadcast tick_changed" in line]
    assert len(matching_logs) == 2
    assert all(
        "user=user-1 habit=habit-1 day=2026-07-11" in line for line in matching_logs
    )
