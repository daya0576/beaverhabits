import datetime
import random
from typing import List

from fastapi import FastAPI, Request
from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend.add_page import add_page_ui
from beaverhabits.frontend.index_page import index_page_ui
from beaverhabits.storage.session_file import DictHabitList
from beaverhabits.storage.storage import HabitList
from beaverhabits.utils import dummy_days

from .storage import session_storage

pick = lambda: random.randint(0, 3) == 0


def dummy_habit_list(days: List[datetime.date]):
    items = [
        {
            "name": name,
            "records": [
                {"day": day.strftime("%Y-%m-%d"), "done": pick()} for day in days
            ],
        }
        for name in ("Order pizz", "Running", "Table Tennis", "Clean", "Call mom")
    ]
    return DictHabitList({"habits": items})


def get_or_create_user_habit_list(days: List[datetime.date]) -> HabitList:
    habit_list = session_storage.get_user_habit_list()
    if habit_list is not None:
        return habit_list

    habit_list = dummy_habit_list(days)
    session_storage.save_user_habit_list(habit_list)
    return habit_list


@ui.page("/")
async def demo(request: Request) -> None:
    days = dummy_days(settings.INDEX_HABIT_ITEM_COUNT)
    habit_list = get_or_create_user_habit_list(days)
    index_page_ui(habit_list, request.scope["root_path"])


@ui.page("/add")
async def demo_add_page(request: Request) -> None:
    days = dummy_days(settings.INDEX_HABIT_ITEM_COUNT)
    habit_list = get_or_create_user_habit_list(days)
    add_page_ui(habit_list, request.scope["root_path"])


def init_demo_routes(fastapi_app: FastAPI):
    ui.run_with(
        fastapi_app,
        mount_path=settings.DEMO_MOUNT_PATH,
        storage_secret=settings.NICEGUI_STORAGE_SECRET,
        dark=True,
    )
