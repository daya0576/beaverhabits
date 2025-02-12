from nicegui import ui

from beaverhabits import views
from beaverhabits.frontend import components
from beaverhabits.frontend.components import (
    HabitAddButton,
    HabitDeleteButton,
    HabitNameInput,
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
        with components.grid(columns=10):
            name = HabitNameInput(item)
            name.classes("col-span-5 break-all")

            goal = WeeklyGoalInput(item, add_ui.refresh)
            goal.classes("col-span-1")

            # Create list selector for existing habit
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
            ).props('dense outlined options-dense').classes("col-span-1")

            star = HabitStarCheckbox(item, add_ui.refresh)
            star.classes("col-span-1")

            delete = HabitDeleteButton(item, habit_list, add_ui.refresh)
            delete.classes("col-span-1")


async def add_page_ui(habit_list: HabitList, user: User):
    async with layout(user=user):
        with ui.column().classes("items-center w-full gap-4"):
            # Add new habit section at the top
            lists = await views.get_user_lists(user)
            list_options = [{"label": "No List", "value": None}] + [
                {"label": list.name, "value": list.id} for list in lists
            ]
            with ui.card().classes("w-full"):
                add = HabitAddButton(habit_list, add_ui.refresh, list_options)
            
            # Existing habits section
            await add_ui(habit_list, lists)
