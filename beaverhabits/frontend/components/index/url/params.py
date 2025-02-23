from typing import Optional, Tuple
from nicegui import context
from sqlalchemy import select

from beaverhabits.logging import logger
from beaverhabits.sql.models import HabitList
from beaverhabits.app.db import get_async_session

def get_list_from_url() -> Tuple[Optional[str | int], Optional[HabitList]]:
    """Get current list ID and details from URL parameters."""
    try:
        # Get list parameter from URL if available
        if not hasattr(context.client.page, "query"):
            logger.debug("No query parameters available")
            return None, None

        current_list_param = context.client.page.query.get("list", "")
        logger.info(f"Raw list parameter from URL: {current_list_param}")
        
        # Handle different list parameter cases
        if current_list_param == "None":
            logger.info("List parameter is 'None' - showing only habits with no list")
            return "None", None
        elif current_list_param.isdigit():
            list_id = int(current_list_param)
            logger.info(f"List parameter is a number: {list_id}")
            return list_id, None  # List details will be fetched later if needed
        else:
            logger.info("No valid list parameter - showing all habits")
            return None, None
    except Exception as e:
        logger.error(f"Error getting list from URL: {e}")
        return None, None

async def get_list_details(list_id: int) -> Optional[HabitList]:
    """Get list details from database."""
    try:
        async with get_async_session() as session:
            stmt = select(HabitList).where(HabitList.id == list_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching list details: {e}")
        return None
