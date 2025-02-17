from nicegui import ui

from beaverhabits import views
from beaverhabits.frontend import components
from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
    HabitSaveButton,
    HabitStarCheckbox,
    WeeklyGoalInput,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList, HabitListBuilder, HabitStatus
from beaverhabits.app.db import User


@ui.refreshable
async def add_ui(habit_list: HabitList, lists: list):
    habits = HabitListBuilder(habit_list).status(HabitStatus.ACTIVE).build()

    for item in habits:
        with ui.card().classes("w-full p-4") as card:
            # Add habit ID to the card for scrolling
            card.props(f'data-habit-id="{item.id}"')
            
            with ui.column().classes("w-full gap-4"):
                # First line: Name (full width)
                with ui.row().classes("w-full"):
                    name = HabitNameInput(item)
                    name.classes("w-full")

                # Second line: Weekly Goal
                with ui.row().classes("items-center gap-2"):
                    goal = WeeklyGoalInput(item, add_ui.refresh)
                    ui.label("times per week")

                # Third line: List Selection (full width)
                list_options = [{"label": "No List", "value": None}] + [
                    {"label": list.name, "value": list.id} for list in lists
                ]
                name_to_id = {"No List": None}
                name_to_id.update({opt["label"]: opt["value"] for opt in list_options[1:]})
                options = list(name_to_id.keys())
                current_name = next(
                    (name for name, id in name_to_id.items() if id == item.list_id),
                    "No List"
                )
                list_select = ui.select(
                    options=options,
                    value=current_name,
                    on_change=lambda e, h=item: setattr(h, 'list_id', name_to_id[e.value])
                ).props('dense outlined options-dense').classes("w-full")

                # Fourth line: Save, Star and Delete buttons (right-aligned)
                with ui.row().classes("w-full justify-end gap-2"):
                    save = HabitSaveButton(item, add_ui.refresh)
                    star = HabitStarCheckbox(item, add_ui.refresh)
                    delete = HabitDeleteButton(item, habit_list, add_ui.refresh)


async def add_page_ui(habit_list: HabitList, user: User):
    async with layout(user=user):
        with ui.column().classes("items-center w-full gap-4"):
            # Add new habit button at the top
            with ui.card().classes("w-full"):
                add = HabitAddButton(habit_list, add_ui.refresh)
            
            # Existing habits section
            await add_ui(habit_list, await views.get_user_lists(user))
