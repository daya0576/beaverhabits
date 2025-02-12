import datetime
import os
from typing import List

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend import javascript
from beaverhabits.frontend.javascript import update_habit_color
from beaverhabits.frontend.components import HabitCheckBox, IndexBadge, link
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import Habit, HabitList, HabitListBuilder, HabitStatus
from beaverhabits.utils import (
    get_week_offset, set_week_offset, reset_week_offset, 
    get_display_days, set_navigating, WEEK_DAYS
)
from beaverhabits.app.db import User


def grid(columns, rows):
    g = ui.grid(columns=columns, rows=rows)
    g.classes("w-full gap-0")
    return g


def check_weekly_goal(habit: Habit, days: list[datetime.date]) -> bool:
    """Check if habit has met its weekly goal for the displayed week"""
    if not habit.weekly_goal:
        return True
    week_ticks = sum(1 for day in days if day in habit.ticked_days)
    return week_ticks >= habit.weekly_goal

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
    left_classes, right_classes = (
        # grid 5
        f"col-span-{name_columns} break-words whitespace-normal",
        # grid 2 2 2 2 2
        f"col-span-{date_columns} px-1 place-self-center",
    )
    header_styles = "font-size: 85%; font-weight: 500; color: #9e9e9e"

    with ui.column().classes("gap-2 w-full max-w-[600px] mx-auto pb-32"):  # Add bottom padding
        # Habit List
        for habit in active_habits:
            with ui.card().classes(row_compat_classes + " w-full max-w-[600px] mx-auto").classes("shadow-none"):
                with ui.column().classes("w-full gap-1"):
                    # Fixed width container
                    with ui.element("div").classes("w-full max-w-[600px] flex justify-start"):
                        # Name row
                        root_path = get_root_path()
                        redirect_page = os.path.join(root_path, "habits", str(habit.id))
                        name = link(habit.name, target=redirect_page)
                        name.classes("break-words whitespace-normal w-full px-4 py-2")
                        name.props(f'data-habit-id="{habit.id}"')
                        name.style(
                            "min-height: 1.5em; height: auto; "
                            f"color: {'lightgreen' if check_weekly_goal(habit, days) else 'orangered'};"
                        )

                    # Checkbox row with fixed width
                    with ui.row().classes("w-full max-w-[600px] gap-2 justify-center items-center flex-nowrap"):
                        ticked_days = set(habit.ticked_days)
                        for day in days:
                            checkbox = HabitCheckBox(habit, day, day in ticked_days, habit_list_ui.refresh)

                        if settings.INDEX_SHOW_HABIT_COUNT:
                            IndexBadge(habit)


@ui.refreshable
async def index_page_ui(days: list[datetime.date], habits: HabitList, user: User | None = None):
    active_habits = HabitListBuilder(habits).status(HabitStatus.ACTIVE).build()
    if not active_habits:
        from beaverhabits.frontend.layout import redirect
        redirect("add")
        return

    async with layout(user=user):
        await week_navigation(days)
        await habit_list_ui(days, active_habits)

    # Initialize JavaScript functions and prevent long press context menu
    ui.context.client.on_connect(javascript.prevent_context_menu)
    ui.context.client.on_connect(javascript.preserve_scroll)
    # Define updateHabitColor function on page load
    def define_update_habit_color():
        ui.run_javascript("""
        window.updateHabitColor = function(habitId, weeklyGoal, currentWeekTicks) {
            const habitLink = document.querySelector(`[data-habit-id="${habitId}"]`);
            if (!habitLink) return;
            
            // Update color based on weekly goal
            if (!weeklyGoal || currentWeekTicks >= weeklyGoal) {
                habitLink.style.color = 'lightgreen';
            } else {
                habitLink.style.color = 'orangered';
            }
        }
        """)
    ui.context.client.on_connect(define_update_habit_color)
