from loguru import logger
from nicegui import background_tasks, core
from nicegui.storage import observables

from beaverhabits.app import crud
from beaverhabits.app.db import User
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import UserStorage


class DatabasePersistentDict(observables.ObservableDict):

    def __init__(self, user: User, data: dict) -> None:
        self.user = user
        super().__init__(data, on_change=self.backup)

    def backup(self) -> None:
        async def async_backup() -> None:
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


class UserDatabaseStorage(UserStorage[DictHabitList]):
    async def get_user_habit_list(self, user: User) -> DictHabitList:
        user_habit_list = await crud.get_user_habit_list(user)
        if user_habit_list is None:
            raise Exception(f"User habit list not found for user {user.email}")

        d = DatabasePersistentDict(user, user_habit_list.data)
        return DictHabitList(d)

    async def init_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        user_habit_list = await crud.get_user_habit_list(user)
        if user_habit_list and user_habit_list.data:
            raise Exception(
                f"User habit list already exists for user {user.email}, cannot overwrite"
            )

        await crud.update_user_habit_list(user, habit_list.data)
