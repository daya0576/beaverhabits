from typing import List as TypeList, Dict, Optional

from nicegui import ui, app
from beaverhabits.configs import settings
from beaverhabits.sql.models import HabitList
from beaverhabits.logging import logger

def handle_list_change(e, name_to_id: Dict[str, Optional[int | str]], path: str) -> None:
    """Handle list selection change."""
    selected_value = e.value
    list_param = name_to_id.get(selected_value)

    # Update storage only if it's a specific list ID or "No List"
    if isinstance(list_param, int) or list_param is None:
        app.storage.user.update({"current_list": list_param})
    elif list_param == "all":
        # Clear storage if "All" is selected
        app.storage.user.pop("current_list", None)

    # Determine target URL
    base_path = path if path.endswith("/add") else settings.GUI_MOUNT_PATH

    if list_param == "all":
        target_url = base_path  # Navigate to base path for "All"
    elif list_param is None:
        target_url = f"{base_path}?list=None" # Explicitly show habits with no list
    else: # Must be an integer ID
        target_url = f"{base_path}?list={list_param}"

    logger.debug(f"List selector - navigating to: {target_url}")
    ui.navigate.to(target_url)

@ui.refreshable
async def list_selector(lists: TypeList[HabitList], current_list_id: int | str | None = None, path: str = "") -> None:
    """Dropdown for selecting current list."""
    with ui.row().classes("items-center gap-2 pt-2 pl-2"):
        # Create name-to-id mapping, starting with "All" and "No List"
        name_to_id: Dict[str, Optional[int | str]] = {"All": "all", "No List": None}
        name_to_id.update({list.name: list.id for list in lists if not list.deleted})

        # Create options list
        options = list(name_to_id.keys())

        # Get current name based on list ID
        current_name = "All" # Default to "All"
        try:
            if isinstance(current_list_id, str) and current_list_id.lower() == "none":
                current_name = "No List"
                logger.info("List selector - using 'No List' for 'None' string value")
            elif isinstance(current_list_id, int):
                # Find name for the integer ID
                found_name = next((name for name, id_val in name_to_id.items() if id_val == current_list_id), None)
                if found_name:
                    current_name = found_name
                    logger.info(f"List selector - found name: {current_name} for ID: {current_list_id}")
                else:
                    logger.warning(f"List selector - ID {current_list_id} not found in lists, defaulting to 'All'")
            elif current_list_id is None:
                 # Explicitly handle None -> "All"
                 current_name = "All"
                 logger.info("List selector - using 'All' for None value (no list parameter)")
            else:
                logger.warning(f"List selector - defaulting to 'All' due to unexpected value: {current_list_id!r}")

        except Exception as e:
            logger.error(f"List selector - error determining current name: {e}")
            current_name = "All" # Fallback to "All" on error

        # Create the select dropdown
        ui.select(
            options=options,
            value=current_name,
            on_change=lambda e: handle_list_change(e, name_to_id, path)
        ).props('outlined').classes('large-dropdown-options') # Add custom class
