import csv
import json
from datetime import datetime
from io import StringIO

from nicegui import events, ui

from beaverhabits import const
from beaverhabits.app.db import User
from beaverhabits.frontend import icons
from beaverhabits.frontend.layout import layout
from beaverhabits.logging import logger
from beaverhabits.sql.models import Habit, HabitList, CheckedRecord
from beaverhabits.app.crud import (
    create_list,
    create_habit,
    get_user_lists,
    get_user_habits,
    toggle_habit_check,
)


async def import_from_json(text: str, user: User) -> list[dict]:
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
    data = json.loads(text)
    if not data.get("habits"):
        raise ValueError("No habits found")
    return data["habits"]


async def import_from_csv(text: str) -> list[dict]:
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

    return habits


async def import_ui_page(user: User | None = None):
    async def handle_upload(e: events.UploadEventArguments):
        try:
            text = e.content.read().decode("utf-8")
            if e.name.endswith(".json"):
                habits_data = await import_from_json(text, user)
            elif e.name.endswith(".csv"):
                habits_data = await import_from_csv(text)
            else:
                raise ValueError("Unsupported format")

            # Get existing habits
            existing_habits = await get_user_habits(user)
            existing_names = {h.name for h in existing_habits}

            # Separate new and existing habits
            new_habits = [h for h in habits_data if h["name"] not in existing_names]
            merge_habits = [h for h in habits_data if h["name"] in existing_names]

            logger.info(f"New habits: {len(new_habits)}")
            logger.info(f"Merge habits: {len(merge_habits)}")

            with ui.dialog() as dialog, ui.card().classes("w-64"):
                ui.label(
                    "Are you sure? "
                    + f"{len(new_habits)} habits will be added and "
                    + f"{len(merge_habits)} habits will be merged.",
                )
                with ui.row():
                    ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
                    ui.button("No", on_click=lambda: dialog.submit("No"))

            result = await dialog
            if result != "Yes":
                return

            # Create a default list for imported habits if none exists
            lists = await get_user_lists(user)
            if not lists:
                default_list = await create_list(user, "Default")
                list_id = default_list.id
            else:
                list_id = lists[0].id

            # Import new habits
            for habit_data in new_habits:
                habit = await create_habit(user, list_id, habit_data["name"])
                # Import records
                for record in habit_data["records"]:
                    day = datetime.strptime(record["day"], "%Y-%m-%d").date()
                    if record["done"]:
                        await toggle_habit_check(habit.id, user.id, day)

            # Merge existing habits
            for habit_data in merge_habits:
                habit = next(h for h in existing_habits if h.name == habit_data["name"])
                # Import records
                for record in habit_data["records"]:
                    day = datetime.strptime(record["day"], "%Y-%m-%d").date()
                    if record["done"]:
                        await toggle_habit_check(habit.id, user.id, day)

            ui.notify(
                f"Imported {len(new_habits) + len(merge_habits)} habits",
                position="top",
                color="positive",
            )
        except json.JSONDecodeError:
            ui.notify("Import failed: Invalid JSON", color="negative", position="top")
        except Exception as error:
            logger.exception("Import failed")
            ui.notify(str(error), color="negative", position="top")

    async with layout(title="Import", with_menu=False, user=user):
        with ui.column().classes("gap-2"):
            # Upload: https://nicegui.io/documentation/upload
            upload = ui.upload(on_upload=handle_upload, max_files=1)
            upload.props('accept=.json,.csv color="grey-10" flat')
            upload.classes("max-w-full")

            # Note
            with ui.row().classes("gap-1"):
                ui.label("Restore your existing setup and continue")
                with ui.link(target=const.IMPORT_WIKI_PAGE, new_tab=True):
                    ui.icon(icons.HELP)
