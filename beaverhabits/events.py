import asyncio
import datetime
from collections import defaultdict
from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar, cast

from beaverhabits.logger import logger


@dataclass(frozen=True)
class TickChanged:
    user_id: str
    habit_id: str
    day: datetime.date
    done: bool
    text: str | None
    timestamp: int


@dataclass(frozen=True)
class HabitListChanged:
    user_id: str
    # Serialized habit list metadata (no records). Passed through verbatim to
    # other connected devices so they can apply it without a full pull.
    payload: dict


Event = TypeVar("Event")
Handler = Callable[[object], Awaitable[None]]
_handlers: dict[type, list[Handler]] = defaultdict(list)
_background_tasks: set[asyncio.Task] = set()


def subscribe(event_type: type[Event]):
    def decorator(handler: Callable[[Event], Awaitable[None]]):
        _handlers[event_type].append(cast(Handler, handler))
        logger.debug(f"Subscribed {handler.__qualname__} to {event_type.__name__}")
        return handler

    return decorator


def publish(event: object) -> None:
    handlers = _handlers[type(event)]
    logger.debug(f"Publishing {type(event).__name__} to {len(handlers)} handler(s)")
    for handler in handlers:
        task = asyncio.create_task(handler(event), name=handler.__qualname__)
        _background_tasks.add(task)
        task.add_done_callback(_on_task_done)


def _on_task_done(task: asyncio.Task) -> None:
    _background_tasks.discard(task)
    if not task.cancelled() and (error := task.exception()):
        logger.error(f"Event handler {task.get_name()} failed: {error}")
