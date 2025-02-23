import datetime
from typing import List

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend.layout import layout
from beaverhabits.sql.models import Habit
from beaverhabits.app.db import User
from beaverhabits.logging import logger
from beaverhabits.frontend.components.index import (
    week_navigation,
    habit_list_ui,
    letter_filter_ui,
    should_show_filter,
    filter_habits_by_list,
    get_list_from_url,
    get_list_details
)

async def index_page_ui(days: list[datetime.date], habits: List[Habit], user: User | None = None):
    """Main index page UI."""
    # Get current list from URL and fetch list details if needed
    current_list_id, current_list = get_list_from_url()
    
    # Get list details if needed
    if isinstance(current_list_id, int):
        current_list = await get_list_details(current_list_id)
        if current_list is None:
            logger.error(f"Could not find list with ID {current_list_id}")

    # Debug logging
    logger.info(f"Current list ID: {current_list_id}")
    logger.info(f"Current list object: {current_list}")
    logger.info(f"All habits: {[(h.id, h.name, h.list_id) for h in habits]}")

    # Filter habits by list
    active_habits = filter_habits_by_list(habits, current_list_id)

    async with layout(user=user):
        with ui.column().classes("w-full"):
            # Determine if letter filter should be enabled
            show_filter = should_show_filter(
                current_list_id,
                current_list,
                settings.ENABLE_LETTER_FILTER
            )
            
            # Initialize letter filter state in JavaScript
            ui.run_javascript(f'window.HabitFilter.setEnabled({str(show_filter).lower()});')
            
            await week_navigation(days)
            if show_filter:
                await letter_filter_ui(active_habits)
            await habit_list_ui(days, active_habits)
