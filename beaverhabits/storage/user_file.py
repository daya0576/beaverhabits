import json
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi_users_db_sqlalchemy import UUID_ID
from nicegui import background_tasks, core, observables

from beaverhabits.app.db import User
from beaverhabits.configs import USER_DATA_FOLDER
from beaverhabits.logging import logger
from beaverhabits.utils import generate_short_hash
from beaverhabits.storage.dict import DictHabit, DictHabitList, DictList
from beaverhabits.storage.storage import UserStorage

KEY_NAME = "data"


class FilePersistentDict(observables.ObservableDict):

    def __init__(
        self, filepath: Path, encoding: Optional[str] = None, *, indent: bool = False
    ) -> None:
        self.filepath = filepath
        self.encoding = encoding
        self.indent = indent
        try:
            data = json.loads(filepath.read_text(encoding)) if filepath.exists() else {}
        except Exception:
            logger.warning(f"Could not load storage file {filepath}")
            data = {}
        super().__init__(data, on_change=self.backup)

    def backup(self) -> None:
        """Back up the data to the given file path."""
        if not self.filepath.exists():
            if not self:
                return
            self.filepath.parent.mkdir(exist_ok=True)

        async def backup() -> None:
            async with aiofiles.open(self.filepath, "w", encoding=self.encoding) as f:
                await f.write(json.dumps(self, indent=self.indent))

        if core.loop:
            background_tasks.create_lazy(backup(), name=self.filepath.stem)
        else:
            core.app.on_startup(backup())


class UserDiskStorage(UserStorage[DictHabitList, DictHabit]):
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

    async def get_user_lists(self, user: User) -> list[DictList]:
        d = self._get_persistent_dict(user)
        lists = d.get("lists", [])
        return [DictList(l) for l in lists]

    async def add_list(self, user: User, name: str) -> DictList:
        d = self._get_persistent_dict(user)
        if "lists" not in d:
            d["lists"] = []
        
        list_data = {"id": generate_short_hash(name), "name": name}
        d["lists"].append(list_data)
        return DictList(list_data)

    async def update_list(self, user: User, list_id: str, name: str) -> None:
        d = self._get_persistent_dict(user)
        for list_data in d.get("lists", []):
            if list_data["id"] == list_id:
                list_data["name"] = name
                break

    async def delete_list(self, user: User, list_id: str) -> None:
        d = self._get_persistent_dict(user)
        
        # Remove list
        d["lists"] = [l for l in d.get("lists", []) if l["id"] != list_id]
        
        # Unassign habits
        habit_list = d.get(KEY_NAME)
        if habit_list:
            for habit in habit_list.get("habits", []):
                if habit.get("list_id") == list_id:
                    habit["list_id"] = None


_user_storage: UserDiskStorage | None = None

def get_user_storage() -> UserDiskStorage:
    """Get the user storage instance."""
    global _user_storage
    if _user_storage is None:
        _user_storage = UserDiskStorage()
    return _user_storage
