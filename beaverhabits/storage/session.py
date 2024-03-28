from typing import Optional
import nicegui
from beaverhabits.app.db import User

from beaverhabits.storage.storage import HabitList, Storage

KEY_NAME = "user_habit_list"


class SessionStorage(Storage):
    def get_user_habit_list(self, user: User) -> Optional[HabitList]:
        user_habit_list = nicegui.app.storage.user.get(KEY_NAME)
        if user_habit_list is not None:
            return user_habit_list

    def save_user_habit_list(self, user: User, habit_list: HabitList) -> None:
        nicegui.app.storage.user[KEY_NAME] = habit_list

    def get_or_create_user_habit_list(
        self, user: User, default_habit_list: HabitList
    ) -> HabitList:
        habit_list = self.get_user_habit_list(user)
        if habit_list is not None and isinstance(habit_list, HabitList):
            return habit_list

        self.save_user_habit_list(user, default_habit_list)
        return default_habit_list
