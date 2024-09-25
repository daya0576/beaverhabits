import json

from nicegui import events, ui

from beaverhabits.app.db import User
from beaverhabits.frontend.components import menu_header
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import HabitList
from beaverhabits.views import user_storage


def import_from_json(text: str) -> HabitList:
    d = json.loads(text)
    habit_list = DictHabitList(d)
    if not habit_list.habits:
        raise ValueError("No habits found")
    return habit_list


def import_ui_page(user: User, from_habit_list: HabitList | None):
    async def handle_upload(e: events.UploadEventArguments):
        text = e.content.read().decode("utf-8")
        to_habit_list = import_from_json(text)
        await user_storage.save_user_habit_list(user, to_habit_list)
        ui.notify(f"Imported {len(to_habit_list.habits)} habits")

    menu_header("Import", target=get_root_path())
    ui.upload(on_upload=handle_upload)
    return
