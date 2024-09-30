from typing import Optional

import nicegui

from .dict import DictHabitList
from .storage import SessionStorage

KEY_NAME = "user_habit_list"


class SessionDictStorage(SessionStorage[DictHabitList]):
    def get_user_habit_list(self) -> Optional[DictHabitList]:
        d = nicegui.app.storage.user.get(KEY_NAME)
        if not d:
            return None
        return DictHabitList(d)

    def save_user_habit_list(self, habit_list: DictHabitList) -> None:
        nicegui.app.storage.user[KEY_NAME] = habit_list.data
