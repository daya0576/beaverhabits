import datetime
from typing import List

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend.components import HabitCheckBox, IndexBadge
from beaverhabits.frontend.components.habit.link import HabitLink
from beaverhabits.frontend.components.habit.goal import HabitGoalLabel
from beaverhabits.frontend.components.habit.priority import HabitPriority
from beaverhabits.sql.models import Habit
from beaverhabits.app.crud import get_habit_checks
from beaverhabits.logging import logger
from .utils import get_habit_priority, get_week_ticks, get_last_week_completion, should_check_last_week

async def update_habit_card(habit: Habit, priority_label: HabitPriority | None = None) -> None:
    """Update a habit card's priority and trigger sort."""
    today = datetime.date.today()
    week_ticks, _ = await get_week_ticks(habit, today)
    is_completed = habit.weekly_goal and week_ticks >= habit.weekly_goal
    priority = await calculate_habit_priority(habit, is_completed)
    
    # Update priority label if provided
    if priority_label:
        await priority_label._update_priority(priority)
    
    # Update card data attribute and sort
    ui.run_javascript(f'''
        const card = document.querySelector('.habit-card[data-habit-id="{habit.id}"]');
        if (card) {{
            card.setAttribute('data-priority', '{priority}');
            window.sortHabits();
        }}
    ''')

@ui.refreshable
async def habit_list_ui(days: list[datetime.date], active_habits: List[Habit]):
    """Habit list component."""
    # Calculate column count
    name_columns, date_columns = settings.INDEX_HABIT_NAME_COLUMNS, 2
    count_columns = 2 if settings.INDEX_SHOW_HABIT_COUNT else 0
    columns = name_columns + len(days) * date_columns + count_columns

    row_compat_classes = "px-0 py-1"

    # Sort habits by priority
    sorted_habits = []
    today = datetime.date.today()
    for habit in active_habits:
        week_ticks, _ = await get_week_ticks(habit, today)
        is_completed = habit.weekly_goal and week_ticks >= habit.weekly_goal
        priority = await calculate_habit_priority(habit, is_completed)
        sorted_habits.append((priority, habit))
    sorted_habits.sort(key=lambda x: x[0])  # Sort by priority
    sorted_habits = [habit for _, habit in sorted_habits]  # Extract just the habits

    container = ui.column().classes("w-full habit-card-container pb-32 px-2 md:px-4")  # Responsive padding
    with container:
        # Habit List
        for habit in sorted_habits:
            await render_habit_card(habit, days, row_compat_classes)

async def calculate_habit_priority(habit: Habit, is_completed: bool = None) -> int:
    """Calculate priority based on today's state and weekly completion."""
    today = datetime.date.today()
    records = await get_habit_checks(habit.id, habit.user_id)
    today_record = next((r for r in records if r.day == today), None)
    
    # If is_completed is provided and True, return highest priority (4)
    if is_completed:
        return 4  # Weekly goal completed (very last)
    
    if today_record:
        today_state = today_record.done
        if today_state is True:
            return 3  # Completed (last)
        elif today_state is False:
            return 2  # Skipped (third)
    return 0  # Not set (first)

async def render_habit_card(habit: Habit, days: list[datetime.date], row_classes: str):
    """Render a single habit card."""
    today = datetime.date.today()
    records = await get_habit_checks(habit.id, habit.user_id)
    week_ticks, _ = await get_week_ticks(habit, today)
    is_completed = habit.weekly_goal and week_ticks >= habit.weekly_goal
    priority = await calculate_habit_priority(habit, is_completed)
    last_week_complete = await get_last_week_completion(habit, today)
    
    card = ui.card().classes(row_classes + " w-full habit-card").classes("shadow-none")
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
                # Calculate color based on completion and creation date
                if not should_check_last_week(habit, today):                    
                    initial_color = (
                        settings.HABIT_COLOR_COMPLETED if is_completed
                        else settings.HABIT_COLOR_INCOMPLETE
                    )
                    
                    #logger.debug(f"Habit {habit.name} is new, color: {initial_color}")
                else:
                    initial_color = (
                        settings.HABIT_COLOR_COMPLETED if is_completed
                        else settings.HABIT_COLOR_LAST_WEEK_INCOMPLETE if not last_week_complete and habit.weekly_goal > 0
                        else settings.HABIT_COLOR_INCOMPLETE
                    )
                    ##logger.debug(f"Habit {habit.name} is existing, color: {initial_color}")
                
                # Container with relative positioning
                with ui.element("div").classes("relative w-full"):
                    # Title container with space for goal
                    with ui.element("div").classes("pr-16"):
                        name = HabitLink(habit.name, target=redirect_page, initial_color=initial_color)
                        name.classes("block break-words whitespace-normal w-full px-3 py-2")
                    
                    # Goal count fixed to top right
                    if habit.weekly_goal:
                        with ui.element("div").classes("absolute top-2 right-4"):
                            goal_label = HabitGoalLabel(habit.weekly_goal, initial_color)
                            goal_label.props(f'data-habit-id="{habit.id}"')
                    
                    show_hide_class = "hidden"
                    if settings.INDEX_SHOW_PRIORITY:
                        show_hide_class = "visible"
                        pass

                    with ui.element("div").classes("absolute top-2 right-16 " + show_hide_class):
                        priority_label = HabitPriority(priority)
                        priority_label.props(f'data-habit-id="{habit.id}"')

                name.props(
                    f'data-habit-id="{habit.id}" '
                    f'data-weekly-goal="{habit.weekly_goal or 0}" '
                    f'data-week-ticks="{week_ticks}" '
                    f'data-last-week-complete="{str(last_week_complete).lower()}"'
                )
                name.style("min-height: 1.5em; height: auto;")

            # Checkbox row with fixed width
            with ui.row().classes("w-full gap-1 justify-start items-center flex-nowrap"):
                for day in days:
                    # Get the actual state from checked_records
                    record = next((r for r in records if r.day == day), None)
                    state = record.done if record else None  # None means not set
                    checkbox = HabitCheckBox(habit, day, state, name, priority_label)

                if settings.INDEX_SHOW_HABIT_COUNT:
                    IndexBadge(habit)
