import datetime
from nicegui import ui

from beaverhabits.utils import get_week_offset, set_week_offset, set_navigating
from beaverhabits.frontend.components.utils.date import format_week_range

@ui.refreshable
async def week_navigation(days: list[datetime.date]):
    """Week navigation component."""
    offset = get_week_offset()
    state = ui.state(dict(can_go_forward=offset < 0))
    
    # Removed w-full, justify-center, mb-2
    with ui.row().classes("items-center gap-4"): 
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
    """Change the current week offset and reload the page."""
    set_week_offset(new_offset)
    set_navigating(True)  # Mark that we're navigating
    # Navigate to the same page to get fresh data
    ui.navigate.reload()
