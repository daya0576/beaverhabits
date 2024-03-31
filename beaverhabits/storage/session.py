from typing import Optional
import nicegui
from beaverhabits.app.db import User

from beaverhabits.storage.storage import CheckedRecord, Habit, HabitList, Storage

KEY_NAME = "user_habit_list"


class SessionHabit(Habit):
    def tick(self, record: CheckedRecord) -> None:
        if record not in self.records:
            self.records.append(record)

    async def update_priority(self, priority: int) -> None:
        self.priority = priority


class SessionHabitList(HabitList):
    def add(self, name: str) -> None:
        self.items.append(SessionHabit(name=name))
        if self.on_change:
            self.on_change()

    def remove(self, item: Habit) -> None:
        self.items.remove(item)
        if self.on_change:
            self.on_change()


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

        if habit_list is None and not isinstance(habit_list, SessionHabitList):
            self.save_user_habit_list(user, default_habit_list)
            habit_list = default_habit_list

        sorted(habit_list.items, key=lambda habit: habit.priority)
        return habit_list
