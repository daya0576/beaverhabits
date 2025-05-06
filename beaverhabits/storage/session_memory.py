import contextvars
from typing import Optional

import nicegui
from cachetools import TTLCache
from fastapi import Request

from beaverhabits.logger import logger

from .dict import DictHabitList
from .storage import SessionStorage

request_contextvar: contextvars.ContextVar[Optional[Request]] = contextvars.ContextVar(
    "request_var", default=None
)

KEY_NAME = "user_habit_list"
MAX_SIZE = 128


def get_session_id() -> str:
    request = nicegui.storage.request_contextvar.get()
    if request is None:
        raise RuntimeError("Request context is not available")

    return request.session["id"]


class SessionDictStorage(SessionStorage[DictHabitList]):
    def __init__(self) -> None:
        self._users = TTLCache(maxsize=MAX_SIZE, ttl=60 * 60)

    def get_user_habit_list(self) -> Optional[DictHabitList]:
        session_id = get_session_id()
        return self._users.get(session_id)

    def save_user_habit_list(self, habit_list: DictHabitList) -> None:
        session_id = get_session_id()
        self._users[session_id] = habit_list
        logger.info(f"Cache size: {len(self._users)}/{MAX_SIZE}")
