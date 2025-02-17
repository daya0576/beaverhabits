import datetime
import os
from typing import List

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend import javascript
from beaverhabits.frontend.components import (
    HabitCheckBox, IndexBadge, link, grid
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import (
    Habit, HabitList, HabitListBuilder, HabitStatus, 
    get_habit_priority, get_week_ticks, get_last_week_completion
)
from beaverhabits.utils import (
    get_week_offset, set_week_offset, reset_week_offset, 
    get_display_days, set_navigating, WEEK_DAYS
)
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
    
    with ui.row().classes("w-full items-center justify-center gap-4 mb-4"):
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

from beaverhabits.logging import logger

@ui.refreshable
async def habit_list_ui(days: list[datetime.date], active_habits: List[Habit], habit_list: HabitList):
    # Calculate column count
    name_columns, date_columns = settings.INDEX_HABIT_NAME_COLUMNS, 2
    count_columns = 2 if settings.INDEX_SHOW_HABIT_COUNT else 0
    columns = name_columns + len(days) * date_columns + count_columns

    row_compat_classes = "px-0 py-1"

    logger.info("\nRendering habits in UI:")
    for habit in active_habits:
        logger.info(f"  {habit.name}: priority {get_habit_priority(habit, days)}")

    container = ui.column().classes("habit-card-container pb-32")  # Add bottom padding
    with container:
        # Habit List
        for habit in active_habits:
            # Calculate priority using shared function
            priority = get_habit_priority(habit, days)
            
            # Calculate state for color and data attributes
            today = datetime.date.today()
            record = habit.record_by(today)
            week_ticks, _ = get_week_ticks(habit, today)
            is_skipped_today = record and record.done is None
            is_completed = habit.weekly_goal and week_ticks >= habit.weekly_goal
            last_week_complete = get_last_week_completion(habit, today)
            
            card = ui.card().classes(row_compat_classes + " w-full habit-card").classes("shadow-none")
            # Add data attributes for sorting
            # Get order if exists
            order = habit_list.order.index(str(habit.id)) if habit_list.order and str(habit.id) in habit_list.order else float("inf")
            card.props(
                f'data-habit-id="{habit.id}" '
                f'data-priority="{priority}" '
                f'data-starred="{int(habit.star)}" '
                f'data-name="{habit.name}" '
                f'data-status="{habit.status.value}" '
                f'data-order="{order}"'
            )
            with card:
                with ui.column().classes("w-full gap-1"):
                    # Fixed width container
                    with ui.element("div").classes("w-full flex justify-start"):
                        # Name row
                        root_path = get_root_path()
                        redirect_page = os.path.join(root_path, "habits", str(habit.id))
                        # Calculate color
                        initial_color = (
                            settings.HABIT_COLOR_SKIPPED if is_skipped_today
                            else settings.HABIT_COLOR_LAST_WEEK_INCOMPLETE if not last_week_complete and habit.weekly_goal > 0
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
                                    goal_label = ui.label(f"{habit.weekly_goal}x").classes("text-sm")
                                    goal_label.style(f"color: {initial_color};")
                            
                            # Priority label if enabled
                            if settings.INDEX_SHOW_PRIORITY:
                                with ui.element("div").classes("absolute top-2 right-16"):
                                    ui.label(f"Priority: {priority}").classes("text-xs text-gray-500 priority-label")

                        name.props(
                            f'data-habit-id="{habit.id}" '
                            f'data-weekly-goal="{habit.weekly_goal or 0}" '
                            f'data-week-ticks="{week_ticks}" '
                            f'data-skipped="{str(is_skipped_today).lower()}" '
                            f'data-last-week-complete="{str(last_week_complete).lower()}"'
                        )
                        name.style(f"min-height: 1.5em; height: auto; color: {initial_color};")

                    # Checkbox row with fixed width
                    with ui.row().classes("w-full gap-2 justify-center items-center flex-nowrap"):
                        ticked_days = set(habit.ticked_days)
                        for day in days:
                            # Get the actual state (checked, unchecked, or skipped)
                            record = habit.record_by(day)
                            state = record.done if record else False
                            checkbox = HabitCheckBox(habit, day, state, habit_list_ui.refresh)

                        if settings.INDEX_SHOW_HABIT_COUNT:
                            IndexBadge(habit)

@ui.refreshable
async def index_page_ui(days: list[datetime.date], habits: HabitList, user: User | None = None):
    # Get active habits and sort them
    active_habits = HabitListBuilder(habits, days=days).status(HabitStatus.ACTIVE).build()

    async with layout(user=user):
        await week_navigation(days)
        await habit_list_ui(days, active_habits, habits)
