import datetime
import json
import random

from fastapi import HTTPException
from nicegui import ui

from beaverhabits.app.db import User
from beaverhabits.logging import logger
from beaverhabits.storage import get_user_dict_storage, session_storage
from beaverhabits.storage.dict import DAY_MASK, DictHabitList
from beaverhabits.storage.storage import Habit, HabitList
from beaverhabits.utils import generate_short_hash

user_storage = get_user_dict_storage()


def dummy_habit_list(days: list[datetime.date]):
    pick = lambda: random.randint(0, 3) == 0
    items = [
        {
            "id": generate_short_hash(name),
            "name": name,
            "records": [
                {"day": day.strftime(DAY_MASK), "done": pick()} for day in days
            ],
        }
        for name in ("Order pizz", "Running", "Table Tennis", "Clean", "Call mom")
    ]
    return DictHabitList({"habits": items})


def get_session_habit_list() -> HabitList | None:
    return session_storage.get_user_habit_list()


async def get_session_habit(habit_id: str) -> Habit:
    habit_list = get_session_habit_list()
    if habit_list is None:
        raise HTTPException(status_code=404, detail="Habit list not found")

    habit = await habit_list.get_habit_by(habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    return habit


def get_or_create_session_habit_list(days: list[datetime.date]) -> HabitList:
    if (habit_list := get_session_habit_list()) is not None:
        return habit_list

    session_storage.save_user_habit_list(dummy_habit_list(days))

    habit_list = get_session_habit_list()
    if habit_list is None:
        raise Exception("Panic! Failed to load habit list")
    return habit_list


async def get_user_habit_list(user: User) -> HabitList | None:
    return await user_storage.get_user_habit_list(user)


async def get_user_habit(user: User, habit_id: str) -> Habit:
    habit_list = await get_user_habit_list(user)
    if habit_list is None:
        raise HTTPException(status_code=404, detail="Habit list not found")

    habit = await habit_list.get_habit_by(habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    return habit


async def get_or_create_user_habit_list(
    user: User, days: list[datetime.date]
) -> HabitList:
    logger.info("Getting user habit list")
    habit_list = await get_user_habit_list(user)
    if habit_list is not None:
        return habit_list

    await user_storage.save_user_habit_list(user, dummy_habit_list(days))

    habit_list = await get_user_habit_list(user)
    if habit_list is None:
        raise Exception("Panic! Failed to load habit list")
    return habit_list


async def export_user_habit_list(habit_list: HabitList, user_identify: str) -> None:
    # json to binary
    now = datetime.datetime.now()
    if isinstance(habit_list, DictHabitList):
        data = {
            "user_email": user_identify,
            "exported_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            **habit_list.data,
        }
        binary_data = json.dumps(data).encode()
        file_name = f"beaverhabits_{now.strftime('%Y_%m_%d')}.json"
        ui.download(binary_data, file_name)
    else:
        ui.notification("Export failed, please try again later.")
