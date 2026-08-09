import asyncio
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
from beaverhabits.storage.storage import HabitListNotFoundError, UserStorage

KEY_NAME = "data"


class FilePersistentDict(observables.ObservableDict):

    def __init__(
        self, filepath: Path, encoding: Optional[str] = None, *, indent: bool = False
    ) -> None:
        self.filepath = filepath
        self.encoding = encoding
        self.indent = indent
        self._deleted = False
        self._io_lock = asyncio.Lock()
        try:
            data = json.loads(filepath.read_text(encoding)) if filepath.exists() else {}
        except Exception as e:
            raise ValueError(f"Could not load storage file {filepath}", e)
        super().__init__(data, on_change=self.backup)

    def backup(self) -> None:
        """Back up the data to the given file path."""
        if self._deleted:
            return

        if not self.filepath.exists():
            if not self:
                return
            self.filepath.parent.mkdir(exist_ok=True)

        async def backup() -> None:
            async with self._io_lock:
                if self._deleted:
                    return
                try:
                    logger.debug(f"Backing up {self.filepath}")
                    content = json.dumps(self, indent=self.indent)
                    assert content, "Content to write should not be empty!"
                except Exception as e:
                    logger.exception(f"Error while backing up {self.filepath}: {e}")
                    return

                async with aiofiles.open(
                    self.filepath, "w", encoding=self.encoding
                ) as f:
                    logger.debug(f"Writing content length: {len(content)}")
                    await f.write(content)

        if core.loop:
            background_tasks.create_lazy(backup(), name=self.filepath.stem)
        else:
            core.app.on_startup(backup())

    async def delete(self) -> None:
        """Stop future backups and permanently remove the backing file."""
        self._deleted = True
        async with self._io_lock:
            self.filepath.unlink(missing_ok=True)


class UserDiskStorage(UserStorage[DictHabitList]):
    def __init__(self):
        self.user: dict[UUID_ID, FilePersistentDict] = {}

    def _get_persistent_dict(self, user: User) -> FilePersistentDict:
        if user.id in self.user:
            return self.user[user.id]

        path = self._path_for(user)
        d = FilePersistentDict(path, encoding="utf-8")

        # Cache the persistent dict
        self.user[user.id] = d

        return d

    @staticmethod
    def _path_for(user: User) -> Path:
        return Path(USER_DATA_FOLDER) / f"{user.email}.json"

    async def get_user_habit_list(self, user: User) -> DictHabitList:
        d = self._get_persistent_dict(user).get(KEY_NAME)
        if not d:
            raise HabitListNotFoundError(
                f"User {user.email} does not have a habit list, cannot load it."
            )
        habit_list = DictHabitList(d)
        habit_list.sync_user_id = str(user.id)
        return habit_list

    async def init_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        d = self._get_persistent_dict(user)
        if d.get(KEY_NAME):
            raise Exception(
                f"User {user.email} already has a habit list, cannot save it."
            )

        d[KEY_NAME] = habit_list.data

    async def delete_user_habit_list(self, user: User) -> None:
        persistent_dict = self.user.pop(user.id, None)
        if persistent_dict is not None:
            await persistent_dict.delete()
            return

        self._path_for(user).unlink(missing_ok=True)
