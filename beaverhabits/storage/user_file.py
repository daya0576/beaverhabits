from pathlib import Path
from typing import Optional

from nicegui.storage import PersistentDict
from beaverhabits.app.db import User
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import UserStorage

KEY_NAME = "data"


class UserDiskStorage(UserStorage[DictHabitList]):
    def get_user_habit_list(self, user: User) -> Optional[DictHabitList]:
        d = self._get_persistent_dict(user).get(KEY_NAME)
        if not d:
            return None
        return DictHabitList(d)

    def save_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        d = self._get_persistent_dict(user)
        d["data"] = habit_list.data

    def _get_persistent_dict(self, user: User) -> PersistentDict:
        path = Path(f".user/{str(user.id)}.json")
        return PersistentDict(path, encoding="utf-8")
