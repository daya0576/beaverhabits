from typing import Optional

from nicegui import background_tasks, core
from nicegui.storage import observables

from beaverhabits.app import crud
from beaverhabits.app.db import User
from beaverhabits.logging import logger
from beaverhabits.storage.dict import DictHabit, DictHabitList, DictList
from beaverhabits.utils import generate_short_hash
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


class UserDatabaseStorage(UserStorage[DictHabitList, DictHabit]):
    async def get_user_habit_list(self, user: User) -> Optional[DictHabitList]:
        user_habit_list = await crud.get_user_habit_list(user)
        if user_habit_list is None:
            return None

        d = DatabasePersistentDict(user, user_habit_list.data)
        return DictHabitList(d)

    async def save_user_habit_list(self, user: User, habit_list: DictHabitList) -> None:
        user_habit_list = await crud.get_user_habit_list(user)
        if user_habit_list and user_habit_list.data:
            logger.warning("User already has a habit list, not overwriting it")
            return

        await crud.update_user_habit_list(user, habit_list.data)

    async def merge_user_habit_list(
        self, user: User, other: DictHabitList
    ) -> DictHabitList:
        current = await self.get_user_habit_list(user)
        if current is None:
            return other

        return await current.merge(other)

    async def get_user_lists(self, user: User) -> list[DictList]:
        user_habit_list = await crud.get_user_habit_list(user)
        if user_habit_list is None:
            return []
        lists = user_habit_list.data.get("lists", [])
        return [DictList(l) for l in lists]

    async def add_list(self, user: User, name: str) -> DictList:
        user_habit_list = await crud.get_user_habit_list(user)
        if user_habit_list is None:
            user_habit_list = {"habits": [], "lists": []}
        
        if "lists" not in user_habit_list.data:
            user_habit_list.data["lists"] = []
        
        list_data = {"id": generate_short_hash(name), "name": name}
        user_habit_list.data["lists"].append(list_data)
        await crud.update_user_habit_list(user, user_habit_list.data)
        return DictList(list_data)

    async def update_list(self, user: User, list_id: str, name: str) -> None:
        user_habit_list = await crud.get_user_habit_list(user)
        if user_habit_list is None:
            return
        
        for list_data in user_habit_list.data.get("lists", []):
            if list_data["id"] == list_id:
                list_data["name"] = name
                await crud.update_user_habit_list(user, user_habit_list.data)
                break

    async def delete_list(self, user: User, list_id: str) -> None:
        user_habit_list = await crud.get_user_habit_list(user)
        if user_habit_list is None:
            return
        
        # Remove list
        user_habit_list.data["lists"] = [
            l for l in user_habit_list.data.get("lists", []) 
            if l["id"] != list_id
        ]
        
        # Unassign habits
        for habit in user_habit_list.data.get("habits", []):
            if habit.get("list_id") == list_id:
                habit["list_id"] = None
        
        await crud.update_user_habit_list(user, user_habit_list.data)
