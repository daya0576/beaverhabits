from nicegui import ui

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
from beaverhabits.sql.models import Habit, HabitList
from beaverhabits.app.crud import get_user_lists, get_user_habits
from beaverhabits.app.db import User


@ui.refreshable
async def add_ui(habits: list[Habit], lists: list[HabitList], user: User):
    # Filter out deleted habits
    active_habits = [h for h in habits if not h.deleted]
    active_habits.sort(key=lambda h: h.order)

    for item in active_habits:
        with ui.card().classes("w-full p-4") as card:
            # Add habit ID to the card for scrolling
            card.props(f'data-habit-id="{item.id}"')
            
            with ui.column().classes("w-full gap-4"):
                # First line: Name (full width)
                with ui.row().classes("w-full"):
                    name = HabitNameInput(item, None)
                    name.classes("w-full")

                # Second line: Weekly Goal
                with ui.row().classes("items-center gap-2"):
                    weekly_goal = WeeklyGoalInput(item, None)
                    ui.label("times per week")

                # Third line: List Selection (full width)
                list_options = [{"label": "No List", "value": None}] + [
                    {"label": list.name, "value": list.id} for list in lists if not list.deleted
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
                    on_change=lambda e, h=item: (setattr(h, 'list_id', name_to_id[e.value]))
                ).props('dense outlined options-dense').classes("w-full")
                list_select.bind_value_from(lambda: next(
                    (name for name, id in name_to_id.items() if id == item.list_id),
                    "No List"
                ))

                # Fourth line: Save button on left, Star and Delete on right
                with ui.row().classes("w-full justify-between items-center"):
                    # Left side - Save button
                    save = HabitSaveButton(item, weekly_goal, add_ui.refresh)
                    
                    # Right side - Star and Delete buttons
                    with ui.row().classes("gap-2 items-center"):
                        star = HabitStarCheckbox(item, add_ui.refresh)
                        delete = HabitDeleteButton(item, add_ui.refresh)


async def add_page_ui(habits: list[Habit], user: User):
    async with layout(user=user):
        with ui.column().classes("items-center w-full gap-4 pb-64"):
            # Add new habit button at the top
            with ui.card().classes("w-full"):
                add = HabitAddButton(user, None, add_ui.refresh)
            
            # Get all lists for the user
            lists = await get_user_lists(user)
            
            # Existing habits section
            await add_ui(habits, lists, user)
