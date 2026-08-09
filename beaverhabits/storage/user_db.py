import asyncio

from loguru import logger
from nicegui import background_tasks, core
from nicegui.storage import observables

from beaverhabits.app import crud
from beaverhabits.app.db import User
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import HabitListNotFoundError, UserStorage


class DatabasePersistentDict(observables.ObservableDict):

    def __init__(self, user: User, data: dict) -> None:
        self.user = user
        self._deleted = False
        self._backup_lock = asyncio.Lock()
        super().__init__(data, on_change=self.backup)

    def backup(self) -> None:
        if self._deleted:
            return

        async def async_backup() -> None:
            async with self._backup_lock:
                if self._deleted:
                    return
                try:
                    await crud.update_user_habit_list(self.user, self)
                except Exception as e:
                    logger.exception(
                        f"[backup]failed to update habit list for user {self.user.email}: {e}"
                    )

        if core.loop and core.loop.is_running():
            background_tasks.create_lazy(
                async_backup(), name=f"backup-{self.user.email}"
            )
        else:
            raise RuntimeError("No event loop found for scheduling backup")

    async def delete(self) -> None:
        """Stop future database backups and wait for any active backup to finish."""
        self._deleted = True
        async with self._backup_lock:
            pass


class UserDatabaseStorage(UserStorage[DictHabitList]):
    def __init__(self) -> None:
        self.user: dict[object, DatabasePersistentDict] = {}

    async def get_user_habit_list(self, user: User) -> DictHabitList:
        if user.id not in self.user:
            user_habit_list = await crud.get_user_habit_list(user)
            if user_habit_list is None:
                raise HabitListNotFoundError(
                    f"User habit list not found for user {user.email}"
                )
            self.user[user.id] = DatabasePersistentDict(user, user_habit_list.data)

        habit_list = DictHabitList(self.user[user.id])
        habit_list.sync_user_id = str(user.id)
        return habit_list

    async def init_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        user_habit_list = await crud.get_user_habit_list(user)
        if user_habit_list and user_habit_list.data:
            raise Exception(
                f"User habit list already exists for user {user.email}, cannot overwrite"
            )

        await crud.update_user_habit_list(user, habit_list.data)

    async def delete_user_habit_list(self, user: User) -> None:
        persistent_dict = self.user.pop(user.id, None)
        if persistent_dict is not None:
            await persistent_dict.delete()
