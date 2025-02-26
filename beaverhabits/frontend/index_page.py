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
    # Get current list ID from URL parameters for UI components
    # Note: Habits are already filtered at the route level
    current_list_id, _ = get_list_from_url()
    
    # If no list ID in URL, try to get from centralized function
    if current_list_id is None:
        from beaverhabits.routes import get_current_list_id
        current_list_id = get_current_list_id()
    
    # Get list details if needed
    current_list = None
    if isinstance(current_list_id, int):
        current_list = await get_list_details(current_list_id)
        if current_list is None:
            logger.error(f"Could not find list with ID {current_list_id}")

    # Use the pre-filtered habits from the route
    active_habits = habits

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
