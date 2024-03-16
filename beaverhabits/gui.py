import random
from typing import Optional
from fastapi.responses import RedirectResponse

from nicegui import APIRouter, app, ui

from .configs import settings
from .models import Habit, HabitList
from .utils import dummy_records
from .frontend.index import habit_list_ui, index_page_ui

router = APIRouter(prefix="/gui")


@router.page("/")
def index():
    habits = HabitList("N", on_change=habit_list_ui)
    index_page_ui(habits)


@router.page("/demo")
def demo():
    habits = HabitList("Habits", on_change=habit_list_ui.refresh)
    for name in ["Order pizz", "Running", "Table Tennis", "Clean", "Call mom"]:
        pick = lambda: random.randint(0, 3) == 0
        days = settings.INDEX_HABIT_ITEM_COUNT
        habit = Habit(name, items=dummy_records(days, pick=pick))
        habits.add(habit)

    index_page_ui(habits)

    # NOTE dark mode will be persistent for each user across tabs and server restarts
    # ui.dark_mode().bind_value(app.storage.user, "dark_mode")
    # ui.checkbox("dark mode").bind_value(app.storage.user, "dark_mode")


@ui.page("/login")
def login() -> Optional[RedirectResponse]:
    def try_login() -> (
        None
    ):  # local function to avoid passing username and password as arguments
        if passwords.get(username.value) == password.value:
            app.storage.user.update({"username": username.value, "authenticated": True})
            ui.navigate.to(
                app.storage.user.get("referrer_path", "/")
            )  # go back to where the user wanted to go
        else:
            ui.notify("Wrong username or password", color="negative")

    if app.storage.user.get("authenticated", False):
        return RedirectResponse("/")
    with ui.card().classes("absolute-center"):
        username = ui.input("Username").on("keydown.enter", try_login)
        password = ui.input("Password", password=True, password_toggle_button=True).on(
            "keydown.enter", try_login
        )
        ui.button("Log in", on_click=try_login)
    return None
