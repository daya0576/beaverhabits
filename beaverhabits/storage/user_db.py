from typing import Optional

from nicegui import background_tasks, core
from nicegui.storage import observables

from beaverhabits.app import crud
from beaverhabits.app.db import User
from beaverhabits.logging import logger
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import UserStorage


class DatabasePersistentDict(observables.ObservableDict):

    def __init__(self, user: User, data: dict) -> None:
        self.user = user
        super().__init__(data, on_change=self.backup)

    def backup(self) -> None:
        async def backup():
            await crud.update_user_habit_list(self.user, self)

        if core.loop:
            background_tasks.create_lazy(backup(), name=self.user.email)
        else:
            core.app.on_startup(backup())


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
