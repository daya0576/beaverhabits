import json
import logging
import csv
from io import StringIO

from nicegui import events, ui

from beaverhabits.app.db import User
from beaverhabits.frontend.components import menu_header
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import HabitList
from beaverhabits.views import user_storage


async def import_from_json(text: str) -> HabitList:
    """Import from JSON

    Example:
    {
        "habits": [
            {
                "name": "habit1",
                "records": [
                    {"day": "2021-01-01", "done": true},
                    {"day": "2021-01-02", "done": false}
                ]
            },
            ...
    """
    habit_list = DictHabitList(json.loads(text))
    if not habit_list.habits:
        raise ValueError("No habits found")
    return habit_list


async def import_from_csv(text: str) -> HabitList:
    """Import from CSV

    Example:
    Date,a,b,c,d,e,
    2024-01-22,-1,-1,-1,-1,
    2024-01-21,2,-1,-1,-1,
    """
    data = []
    reader = csv.DictReader(StringIO(text))
    for row in reader:
        data.append(row)

    headers = list(data[0].keys())

    habits = []
    for habit_name in headers[1:]:
        if not habit_name:
            continue
        habit = {"name": habit_name, "records": []}
        for row in data:
            day = row["Date"]
            done = True if row[habit_name] and int(row[habit_name]) > 0 else False
            habit["records"].append({"day": day, "done": done})
        habits.append(habit)

    output = {"habits": habits}
    return DictHabitList(output)


def import_ui_page(user: User):
    async def handle_upload(e: events.UploadEventArguments):
        try:
            text = e.content.read().decode("utf-8")
            if e.name.endswith(".json"):
                other = await import_from_json(text)
            elif e.name.endswith(".csv"):
                other = await import_from_csv(text)
            else:
                raise ValueError("Unsupported format")

            from_habit_list = await user_storage.get_user_habit_list(user)
            if not from_habit_list:
                added = other.habits
                merged = set()
                unchanged = set()
            else:
                added = set(other.habits) - set(from_habit_list.habits)
                merged = set(other.habits) & set(from_habit_list.habits)
                unchanged = set(from_habit_list.habits) - set(other.habits)

            logging.info(f"added: {added}")
            logging.info(f"merged: {merged}")
            logging.info(f"unchanged: {unchanged}")

            with ui.dialog() as dialog, ui.card().classes("w-64"):
                ui.label(
                    "Are you sure? "
                    + f"{len(added)} habits will be added and "
                    + f"{len(merged)} habits will be merged.",
                )
                with ui.row():
                    ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
                    ui.button("No", on_click=lambda: dialog.submit("No"))

            result = await dialog
            if result != "Yes":
                return

            to_habit_list = await user_storage.merge_user_habit_list(user, other)
            await user_storage.save_user_habit_list(user, to_habit_list)
            ui.notify(
                f"Imported {len(added) + len(merged)} habits",
                position="top",
                color="positive",
            )
        except json.JSONDecodeError:
            ui.notify("Import failed: Invalid JSON", color="negative", position="top")
        except Exception as error:
            logging.exception("Import failed")
            ui.notify(str(error), color="negative", position="top")

    menu_header("Import", target=get_root_path())

    # Upload: https://nicegui.io/documentation/upload
    upload = ui.upload(on_upload=handle_upload, max_files=1)
    upload.props('accept=.json,.csv label="Upload files" flat text-color="black"')
    upload.classes("w-80 no-shadow")
    return
