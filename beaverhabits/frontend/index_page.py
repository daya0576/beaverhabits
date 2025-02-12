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
from beaverhabits.storage.storage import Habit, HabitList, HabitListBuilder, HabitStatus
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

@ui.refreshable
async def habit_list_ui(days: list[datetime.date], active_habits: List[Habit]):
    # Calculate column count
    name_columns, date_columns = settings.INDEX_HABIT_NAME_COLUMNS, 2
    count_columns = 2 if settings.INDEX_SHOW_HABIT_COUNT else 0
    columns = name_columns + len(days) * date_columns + count_columns

    row_compat_classes = "px-0 py-1"

    container = ui.column().classes("habit-card-container pb-32")  # Add bottom padding
    with container:
        # Habit List
        for habit in active_habits:
            # Calculate priority score for initial sorting
            today = datetime.date.today()
            record = habit.record_by(today)
            week_ticks = sum(1 for day in days if day in habit.ticked_days)
            is_skipped_today = record and record.done is None
            is_completed = habit.weekly_goal and week_ticks >= habit.weekly_goal
            has_ticks = bool(habit.ticked_days)
            
            # Priority: 0=no ticks, 1=some ticks, 2=skipped today, 3=completed
            priority = 3 if is_completed else (2 if is_skipped_today else (1 if has_ticks else 0))
            
            card = ui.card().classes(row_compat_classes + " w-full habit-card").classes("shadow-none")
            # Add data attributes for sorting
            card.props(
                f'data-habit-id="{habit.id}" '
                f'data-priority="{priority}" '
                f'data-starred="{int(habit.star)}" '
                f'data-name="{habit.name}"'
            )
            with card:
                with ui.column().classes("w-full gap-1"):
                    # Fixed width container
                    with ui.element("div").classes("w-full flex justify-start"):
                        # Name row
                        root_path = get_root_path()
                        redirect_page = os.path.join(root_path, "habits", str(habit.id))
                        name = link(habit.name, target=redirect_page)
                        name.classes("break-words whitespace-normal w-full px-4 py-2")
                        name.props(f'data-habit-id="{habit.id}"')
                        name.style("min-height: 1.5em; height: auto;")

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
    # Get active habits
    active_habits = HabitListBuilder(habits).status(HabitStatus.ACTIVE).build()
    
    # Sort habits by priority, star status, and name
    def get_priority(habit: Habit) -> int:
        today = datetime.date.today()
        record = habit.record_by(today)
        week_ticks = sum(1 for day in days if day in habit.ticked_days)
        is_skipped_today = record and record.done is None
        is_completed = habit.weekly_goal and week_ticks >= habit.weekly_goal
        has_ticks = bool(habit.ticked_days)
        
        # Priority: 0=no ticks, 1=some ticks, 2=skipped today, 3=completed
        if is_completed:
            return 3
        elif is_skipped_today:
            return 2
        elif has_ticks:
            return 1
        return 0
    
    active_habits.sort(key=lambda h: (get_priority(h), not h.star, h.name.lower()))
    if not active_habits:
        from beaverhabits.frontend.layout import redirect
        redirect("add")
        return

    async with layout(user=user):
        await week_navigation(days)
        await habit_list_ui(days, active_habits)

    # Initialize JavaScript functions
    ui.context.client.on_connect(javascript.prevent_context_menu)
    ui.context.client.on_connect(javascript.preserve_scroll)
    ui.context.client.on_connect(javascript.update_habit_color)
