import random

from fastapi import FastAPI, Request
from nicegui import ui

from beaverhabits.app.db import User
from beaverhabits.configs import settings
from beaverhabits.frontend.add_page import add_page_ui, add_ui
from beaverhabits.frontend.index_page import index_page_ui
from beaverhabits.storage.session import SessionHabit
from beaverhabits.storage.storage import HabitList
from beaverhabits.utils import dummy_records

from .storage import session_storage


def dummy_habit_list():
    items = []
    for name in ["Order pizz", "Running", "Table Tennis", "Clean", "Call mom"]:
        pick = lambda: random.randint(0, 3) == 0
        days = settings.INDEX_HABIT_ITEM_COUNT
        habit = SessionHabit(name=name, records=dummy_records(days, pick=pick))
        items.append(habit)
    return HabitList(items=items)


@ui.page("/")
async def demo(request: Request) -> None:
    habit_list = dummy_habit_list()
    habit_list = session_storage.get_or_create_user_habit_list(User(), habit_list)
    index_page_ui(habit_list, request.scope["root_path"])


@ui.page("/add")
async def demo_add_page(request: Request) -> None:
    habit_list = dummy_habit_list()
    habit_list = session_storage.get_or_create_user_habit_list(User(), habit_list)
    habit_list.on_change = add_ui.refresh
    add_page_ui(habit_list, request.scope["root_path"])


def init_demo_routes(fastapi_app: FastAPI):
    ui.run_with(
        fastapi_app,
        mount_path="/demo",  # NOTE this can be omitted if you want the paths passed to @ui.page to be at the root
        storage_secret="secret",
        dark=True,
    )
