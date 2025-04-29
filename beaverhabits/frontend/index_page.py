import datetime
from typing import List

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend.layout import layout
from beaverhabits.sql.models import Habit
from beaverhabits.app.db import User
from beaverhabits.logging import logger
from beaverhabits.frontend.components.index import (
    habit_list_ui,
    letter_filter_ui,
    should_show_filter,
    filter_habits_by_list,
    get_list_from_url,
    get_list_details
)

async def index_page_ui(days: list[datetime.date], habits: List[Habit], user: User | None = None, current_list_id: str | int | None = None):
    """Main index page UI."""
    # Note: Habits are already filtered at the route level
    # If no list ID provided, try to get from URL or centralized function
    if current_list_id is None:
        # Try to get from URL
        current_list_id, _ = get_list_from_url()
        
        # If still None, try to get from centralized function
        if current_list_id is None:
            from beaverhabits.routes import get_current_list_id
            current_list_id = get_current_list_id()
            
    logger.info(f"Index page UI - Using list ID: {current_list_id!r}")
    
    # Get list details if needed
    current_list = None
    if isinstance(current_list_id, int):
        current_list = await get_list_details(current_list_id)
        if current_list is None:
            logger.error(f"Could not find list with ID {current_list_id}")

    # Use the pre-filtered habits from the route
    active_habits = habits

    # Pass days to layout
    async with layout(user=user, current_list_id=current_list_id, days=days): 
        with ui.column().classes("w-full"):
            # Determine if letter filter should be enabled
            show_filter = should_show_filter(
                current_list_id,
                current_list,
                settings.ENABLE_LETTER_FILTER
            )
            
            
            # Initialize letter filter state in JavaScript
            ui.run_javascript(f'window.HabitFilter.setEnabled({str(show_filter).lower()});')
            
            if show_filter:
                await letter_filter_ui(active_habits)
            await habit_list_ui(days, active_habits)
