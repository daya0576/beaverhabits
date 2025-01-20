from pathlib import Path
from typing import Optional

from fastapi_users_db_sqlalchemy import UUID_ID
from nicegui.persistence import FilePersistentDict

from beaverhabits.app.db import User
from beaverhabits.configs import USER_DATA_FOLDER
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import UserStorage

KEY_NAME = "data"


class UserDiskStorage(UserStorage[DictHabitList]):
    def __init__(self):
        self.user: dict[UUID_ID, FilePersistentDict] = {}

    def _get_persistent_dict(self, user: User) -> FilePersistentDict:
        if user.id in self.user:
            return self.user[user.id]

        path = Path(f"{USER_DATA_FOLDER}/{str(user.email)}.json")
        d = FilePersistentDict(path, encoding="utf-8")

        # Cache the persistent dict
        self.user[user.id] = d

        return d

    async def get_user_habit_list(self, user: User) -> Optional[DictHabitList]:
        d = self._get_persistent_dict(user).get(KEY_NAME)
        if not d:
            return None
        return DictHabitList(d)

    async def save_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        d = self._get_persistent_dict(user)
        d[KEY_NAME] = habit_list.data

    async def merge_user_habit_list(
        self, user: User, other: DictHabitList
    ) -> DictHabitList:
        current = await self.get_user_habit_list(user)
        if current is None:
            return other

        return await current.merge(other)
