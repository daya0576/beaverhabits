import json
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi_users_db_sqlalchemy import UUID_ID
from nicegui import background_tasks, core, observables

from beaverhabits.app.db import User
from beaverhabits.configs import USER_DATA_FOLDER
from beaverhabits.logging import logger
from beaverhabits.storage.dict import DictHabitList
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
        except Exception as e:
            raise ValueError(f"Could not load storage file {filepath}", e)
        super().__init__(data, on_change=self.backup)

    def backup(self) -> None:
        """Back up the data to the given file path."""
        if not self.filepath.exists():
            if not self:
                return
            self.filepath.parent.mkdir(exist_ok=True)

        async def backup() -> None:
            async with aiofiles.open(self.filepath, "w", encoding=self.encoding) as f:
                logger.debug(f"Backing up {self.filepath}")
                content = json.dumps(self, indent=self.indent)
                if not content:
                    raise ValueError("Empty content to write!!!")
                await f.write(content)

        if core.loop:
            background_tasks.create_lazy(backup(), name=self.filepath.stem)
        else:
            core.app.on_startup(backup())


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
        if d.get(KEY_NAME):
            logger.warning(
                f"Failed to save habit list for user {user.email} because it already exists"
            )
            return
        d[KEY_NAME] = habit_list.data

    async def merge_user_habit_list(
        self, user: User, other: DictHabitList
    ) -> DictHabitList:
        current = await self.get_user_habit_list(user)
        if current is None:
            return other

        return await current.merge(other)
