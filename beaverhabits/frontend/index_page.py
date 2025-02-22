import datetime
import os
from typing import List

from nicegui import ui, context, app

from beaverhabits.configs import settings
from beaverhabits.frontend import javascript
from beaverhabits.frontend.components import (
    HabitCheckBox, IndexBadge, link, grid
)
from beaverhabits.frontend.layout import layout
from beaverhabits.sql.models import Habit
from beaverhabits.app.crud import get_habit_checks
from beaverhabits.utils import (
    get_week_offset, set_week_offset, reset_week_offset, 
    get_display_days, set_navigating, WEEK_DAYS
)
from beaverhabits.logging import logger
from beaverhabits.app.db import User

def format_week_range(days: list[datetime.date]) -> str:
    if not days:
        return ""
    start, end = days[0], days[-1]
    if start.month == end.month:
        return f"{start.strftime('%b %d')} - {end.strftime('%d')}"
    return f"{start.strftime('%b %d')} - {end.strftime('%b %d')}"

@ui.refreshable
async def week_navigation(days: list[datetime.date]):
    offset = get_week_offset()
    state = ui.state(dict(can_go_forward=offset < 0))
    
    with ui.row().classes("w-full items-center justify-center gap-4 mb-2"):
        ui.button(
            "←",
            on_click=lambda: change_week(offset - 1)
        ).props('flat')
        ui.label(format_week_range(days)).classes("text-lg")
        ui.button(
            "→",
            on_click=lambda: change_week(offset + 1)
        ).props('flat').bind_enabled_from(state, 'can_go_forward')

async def change_week(new_offset: int) -> None:
    set_week_offset(new_offset)
    set_navigating(True)  # Mark that we're navigating
    # Navigate to the same page to get fresh data
    ui.navigate.reload()

async def get_habit_priority(habit: Habit, days: List[datetime.date]) -> int:
    """Calculate habit priority based on completion status."""
    records = await get_habit_checks(habit.id, habit.user_id)
    week_ticks = sum(1 for record in records if record.day in days and record.done)
    return 1 if week_ticks >= (habit.weekly_goal or 0) else 0

async def get_week_ticks(habit: Habit, today: datetime.date) -> tuple[int, int]:
    """Get the number of ticks for the current week."""
    records = await get_habit_checks(habit.id, habit.user_id)
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    week_ticks = sum(1 for record in records 
                    if week_start <= record.day <= week_end and record.done)
    total_ticks = sum(1 for record in records if record.done)
    return week_ticks, total_ticks

async def get_last_week_completion(habit: Habit, today: datetime.date) -> bool:
    """Check if the habit was completed last week."""
    records = await get_habit_checks(habit.id, habit.user_id)
    last_week_start = today - datetime.timedelta(days=today.weekday() + 7)
    last_week_end = last_week_start + datetime.timedelta(days=6)
    last_week_ticks = sum(1 for record in records 
                         if last_week_start <= record.day <= last_week_end and record.done)
    return last_week_ticks >= (habit.weekly_goal or 0)

@ui.refreshable
async def habit_list_ui(days: list[datetime.date], active_habits: List[Habit]):
    # Calculate column count
    name_columns, date_columns = settings.INDEX_HABIT_NAME_COLUMNS, 2
    count_columns = 2 if settings.INDEX_SHOW_HABIT_COUNT else 0
    columns = name_columns + len(days) * date_columns + count_columns

    row_compat_classes = "px-0 py-1"

    container = ui.column().classes("w-full habit-card-container pb-32 px-4")  # Add padding
    with container:
        # Habit List
        for habit in active_habits:
            # Calculate priority using shared function
            priority = await get_habit_priority(habit, days)
            
            # Calculate state for color and data attributes
            today = datetime.date.today()
            records = await get_habit_checks(habit.id, habit.user_id)
            today_record = next((r for r in records if r.day == today), None)
            week_ticks, _ = await get_week_ticks(habit, today)
            is_completed = habit.weekly_goal and week_ticks >= habit.weekly_goal
            last_week_complete = await get_last_week_completion(habit, today)
            
            card = ui.card().classes(row_compat_classes + " w-full habit-card").classes("shadow-none")
            # Add data attributes for sorting
            card.props(
                f'data-habit-id="{habit.id}" '
                f'data-priority="{priority}" '
                f'data-starred="{int(habit.star)}" '
                f'data-name="{habit.name}" '
                f'data-order="{habit.order}"'
            )
            with card:
                with ui.column().classes("w-full gap-1"):
                    # Fixed width container
                    with ui.element("div").classes("w-full flex justify-start"):
                        # Name row
                        redirect_page = f"{settings.GUI_MOUNT_PATH}/habits/{habit.id}"
                        # Calculate color
                        initial_color = (
                            settings.HABIT_COLOR_LAST_WEEK_INCOMPLETE if not last_week_complete and habit.weekly_goal > 0
                            else settings.HABIT_COLOR_COMPLETED if is_completed
                            else settings.HABIT_COLOR_INCOMPLETE
                        )
                        
                        # Container with relative positioning
                        with ui.element("div").classes("relative w-full"):
                            # Title container with space for goal
                            with ui.element("div").classes("pr-16"):
                                name = link(habit.name, target=redirect_page)
                                name.classes("block break-words whitespace-normal w-full px-4 py-2")
                            
                            # Goal count fixed to top right
                            if habit.weekly_goal:
                                with ui.element("div").classes("absolute top-2 right-4"):
                                    goal_label = ui.label(f"{int(habit.weekly_goal)}x").classes("text-sm")
                                    goal_label.style(f"color: {initial_color};")
                            
                            # Priority label if enabled
                            if settings.INDEX_SHOW_PRIORITY:
                                with ui.element("div").classes("absolute top-2 right-16"):
                                    ui.label(f"Priority: {priority}").classes("text-xs text-gray-500 priority-label")

                        name.props(
                            f'data-habit-id="{habit.id}" '
                            f'data-weekly-goal="{habit.weekly_goal or 0}" '
                            f'data-week-ticks="{week_ticks}" '
                            f'data-last-week-complete="{str(last_week_complete).lower()}"'
                        )
                        name.style(f"min-height: 1.5em; height: auto; color: {initial_color};")

                    # Checkbox row with fixed width
                    with ui.row().classes("w-full gap-2 justify-center items-center flex-nowrap"):
                        for day in days:
                            # Get the actual state from checked_records
                            record = next((r for r in records if r.day == day), None)
                            state = record.done if record else None  # None means not set
                            checkbox = HabitCheckBox(habit, day, state, habit_list_ui.refresh)

                        if settings.INDEX_SHOW_HABIT_COUNT:
                            IndexBadge(habit)

@ui.refreshable
async def letter_filter_ui(active_habits: List[Habit]):
    # Get unique first letters
    available_letters = sorted(set(habit.name[0].upper() for habit in active_habits))
    
    with ui.row().classes("w-full justify-center gap-2 mb-2"):
        for letter in available_letters:
            ui.button(
                letter,
                on_click=lambda l=letter: ui.run_javascript(
                    f'filterHabits("{l}");'
                )
            ).props('flat dense').classes('letter-filter-btn')

async def index_page_ui(days: list[datetime.date], habits: List[Habit], user: User | None = None):
    # Get current list from storage
    current_list = app.storage.user.get("current_list")

    # Filter habits by list and active status
    active_habits = [h for h in habits if not h.deleted and (
        # Show habit if:
        # - No list is selected and habit has no list
        (current_list is None and h.list_id is None) or
        # - A list is selected and habit belongs to that list
        (current_list is not None and h.list_id == current_list)
    )]
    active_habits.sort(key=lambda h: h.order)

    async with layout(user=user):
        with ui.column().classes("w-full"):
            # Add habit-filter.js to the page if feature is enabled
            if settings.ENABLE_LETTER_FILTER:
                ui.add_head_html(
                    '<script src="/statics/js/habit-filter.js"></script>'
                )
            await week_navigation(days)
            if settings.ENABLE_LETTER_FILTER:
                await letter_filter_ui(active_habits)
            await habit_list_ui(days, active_habits)
