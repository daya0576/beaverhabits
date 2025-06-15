import json
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi_users_db_sqlalchemy import UUID_ID
from nicegui import background_tasks, core, observables

from beaverhabits.app.db import User
from beaverhabits.configs import USER_DATA_FOLDER
from beaverhabits.logger import logger
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
            try:
                logger.debug(f"Backing up {self.filepath}")
                content = json.dumps(self, indent=self.indent)
                assert content, "Content to write should not be empty!"
            except Exception as e:
                logger.exception(f"Error while backing up {self.filepath}: {e}")
                return

            async with aiofiles.open(self.filepath, "w", encoding=self.encoding) as f:
                logger.debug(f"Writing content length: {len(content)}")
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

    async def get_user_habit_list(self, user: User) -> DictHabitList:
        d = self._get_persistent_dict(user).get(KEY_NAME)
        if not d:
            raise Exception(
                f"User {user.email} does not have a habit list, cannot load it."
            )
        return DictHabitList(d)

    async def init_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        d = self._get_persistent_dict(user)
        if d.get(KEY_NAME):
            raise Exception(
                f"User {user.email} already has a habit list, cannot save it."
            )

        d[KEY_NAME] = habit_list.data
