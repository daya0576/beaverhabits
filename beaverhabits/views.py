import datetime
import random
from typing import List, Optional

from beaverhabits.app.db import User
from beaverhabits.storage.dict import DAY_MASK, DictHabitList
from beaverhabits.storage.storage import HabitList
from beaverhabits.storage import get_user_storage, session_storage

user_storage = get_user_storage()


def dummy_habit_list(days: List[datetime.date]):
    pick = lambda: random.randint(0, 3) == 0
    items = [
        {
            "name": name,
            "records": [
                {"day": day.strftime(DAY_MASK), "done": pick()} for day in days
            ],
        }
        for name in ("Order pizz", "Running", "Table Tennis", "Clean", "Call mom")
    ]
    return DictHabitList({"habits": items})


def get_session_habit_list() -> Optional[HabitList]:
    return session_storage.get_user_habit_list()


def get_or_create_session_habit_list(days: List[datetime.date]) -> HabitList:
    if (habit_list := get_session_habit_list()) is not None:
        return habit_list

    habit_list = dummy_habit_list(days)
    session_storage.save_user_habit_list(habit_list)
    return habit_list


async def get_user_habit_list(user: User) -> Optional[HabitList]:
    return await user_storage.get_user_habit_list(user)


async def get_or_create_user_habit_list(
    user: User, days: List[datetime.date]
) -> HabitList:
    habit_list = await get_user_habit_list(user)
    if habit_list is not None:
        return habit_list

    habit_list = dummy_habit_list(days)
    await user_storage.save_user_habit_list(user, habit_list)
    return habit_list
