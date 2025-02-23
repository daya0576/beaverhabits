import os
from nicegui import ui

from beaverhabits.configs import settings

def redirect(x: str) -> None:
    """Navigate to a path under the GUI mount path."""
    ui.navigate.to(os.path.join(settings.GUI_MOUNT_PATH, x))

def open_tab(x: str) -> None:
    """Open a path under the GUI mount path in a new tab."""
    ui.navigate.to(os.path.join(settings.GUI_MOUNT_PATH, x), new_tab=True)

def get_page_title(path: str, default_title: str | None = None) -> str:
    """Get the page title based on the current path."""
    if path == settings.GUI_MOUNT_PATH:
        return default_title or "Beaver Habits"
        
    if "/add" in path:
        return "Add Habit"
    elif "/lists" in path:
        return "Configure Lists"
    elif "/order" in path:
        return "Reorder Habits"
    elif "/import" in path:
        return "Import"
    elif "/export" in path:
        return "Export"
    elif "/habits/" in path:
        return "Habit Details"
    else:
        return default_title or "Beaver Habits"
