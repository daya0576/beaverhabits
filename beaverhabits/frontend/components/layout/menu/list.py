from typing import List as TypeList, Dict, Optional

from nicegui import ui, app
from beaverhabits.configs import settings
from beaverhabits.sql.models import HabitList
from beaverhabits.logging import logger

def handle_list_change(e, name_to_id: Dict[str, Optional[int]], path: str) -> None:
    """Handle list selection change."""
    # Update storage
    app.storage.user.update({"current_list": name_to_id[e.value]})
    
    # Get list parameter
    list_param = name_to_id[e.value]
    
    # Determine target URL
    if path.endswith("/add"):
        # For add page
        target_url = f"{path}?list={list_param}" if list_param is not None else f"{path}?list=None"
    else:
        # For main page
        target_url = f"{settings.GUI_MOUNT_PATH}?list={list_param}" if list_param is not None else f"{settings.GUI_MOUNT_PATH}?list=None"
    
    logger.debug(f"List selector - navigating to: {target_url}")
    ui.navigate.to(target_url)

@ui.refreshable
async def list_selector(lists: TypeList[HabitList], current_list_id: int | None = None, path: str = "") -> None:
    """Dropdown for selecting current list."""
    with ui.row().classes("items-center gap-2"):
        # Create name-to-id mapping
        name_to_id = {"No List": None}
        name_to_id.update({list.name: list.id for list in lists if not list.deleted})
        
        # Create options list
        options = list(name_to_id.keys())
        
        # Get current name based on list ID
        try:
            if current_list_id == "None":
                current_name = "No List"
                logger.debug("List selector - using 'No List'")
            elif isinstance(current_list_id, int):
                # Direct integer value
                current_name = next(
                    (name for name, id in name_to_id.items() if id == current_list_id),
                    "No List"
                )
                logger.debug(f"List selector - found name: {current_name} for ID: {current_list_id}")
            else:
                current_name = "No List"
                logger.debug(f"List selector - defaulting to 'No List' for value: {current_list_id!r}")
        except (AttributeError, ValueError) as e:
            logger.error(f"List selector - error parsing list ID: {e}")
            current_name = "No List"
        
        # Log debug info
        logger.debug(f"List options: {options}")
        logger.debug(f"Current list ID: {current_list_id}")
        logger.debug(f"Current name: {current_name}")
        
        ui.select(
            options=options,
            value=current_name,
            on_change=lambda e: handle_list_change(e, name_to_id, path)
        ).props('outlined dense options-dense')
