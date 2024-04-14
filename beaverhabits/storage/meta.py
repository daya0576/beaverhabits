from typing import Optional
from nicegui import context


ROOT_PATH_KEY = "root_path"
ROOT_PATH_DEFAULT = "/"

DEMO_ROOT_PATH = "/demo"
GUI_ROOT_PATH = "/gui"


def get_root_path() -> str:
    path = context.get_client().page.path
    return DEMO_ROOT_PATH if path.startswith(DEMO_ROOT_PATH) else GUI_ROOT_PATH


def get_page_title(path: Optional[str] = None) -> str:
    path = path or context.get_client().page.path
    return "Demo" if path.startswith(DEMO_ROOT_PATH) else "Habits"
