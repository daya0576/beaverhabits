import datetime
from beaverhabits.configs import settings
from beaverhabits.sql.models import Habit
from beaverhabits.api.models import HabitSorting, HabitUpdateResponse
from beaverhabits.logging import logger
from beaverhabits.app.crud import get_habit_checks
from .utils import get_week_ticks, get_last_week_completion, should_check_last_week, get_habit_priority

async def get_habit_state(habit: Habit, today: datetime.date) -> HabitUpdateResponse:
    """Calculate the current state of a habit including color and sorting info."""
    # Get completion status
    week_ticks, _ = await get_week_ticks(habit, today)
    is_completed = habit.weekly_goal and week_ticks >= habit.weekly_goal
    last_week_complete = await get_last_week_completion(habit, today)
    priority = await get_habit_priority(habit, [today])

    # Get today's record
    records = await get_habit_checks(habit.id, habit.user_id)
    today_record = next((r for r in records if r.day == today), None)
    
    logger.debug(f"Checking state for habit {habit.name}:")
    logger.debug(f"  - Today's record: {today_record!r}")
    logger.debug(f"  - Week ticks: {week_ticks}")
    logger.debug(f"  - Weekly goal: {habit.weekly_goal}")
    logger.debug(f"  - Is completed: {is_completed}")
    logger.debug(f"  - Last week complete: {last_week_complete}")
    logger.debug(f"  - Priority: {priority}")

    # Determine state based on today's record
    if today_record:
        state = (
            "skipped" if today_record.done is False
            else "checked" if today_record.done is True
            else "unset"
        )
    else:
        state = "unset"
    logger.debug(f"  - Today's state: {state}")

    # Calculate color based on state and completion
    if state == "skipped":
        color = settings.HABIT_COLOR_SKIPPED
        priority = 3  # Lower priority = shown last
    else:
        # Calculate color based on completion and creation date
        if not should_check_last_week(habit, today):
            # New habit - only check current week
            color = (
                settings.HABIT_COLOR_COMPLETED if is_completed
                else settings.HABIT_COLOR_INCOMPLETE
            )
            logger.debug(f"Habit {habit.name} is new - setting color: {color}")
        else:
            # Existing habit - check both weeks
            color = (
                settings.HABIT_COLOR_COMPLETED if is_completed
                else settings.HABIT_COLOR_LAST_WEEK_INCOMPLETE if not last_week_complete and habit.weekly_goal > 0
                else settings.HABIT_COLOR_INCOMPLETE
            )
            logger.debug(f"Habit {habit.name} is existing - setting color: {color}")

    # Create sorting info
    sorting = HabitSorting(
        starred=habit.star,
        priority=priority,
        order=habit.order,
        name=habit.name
    )
    logger.debug(f"Created sorting info: {sorting.model_dump_json()}")

    response = HabitUpdateResponse(
        habit_id=habit.id,
        color=color,
        state=state,
        sorting=sorting
    )
    logger.debug(f"Returning state: {response.model_dump_json()}")
    return response
