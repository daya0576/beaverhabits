from nicegui import ui
from nicegui.testing import Screen

from beaverhabits.configs import settings
from beaverhabits.frontend.index_page import index_page_ui
from beaverhabits.utils import dummy_days
from beaverhabits.views import (
    get_or_create_session_habit_list,
)

# Test cases:
# https://github.com/zauberzeug/nicegui/tree/main/tests


def test_hello():
    assert "Hello" == "Hello"


def test_demo_page(screen: Screen) -> None:
    @ui.page("/demo")
    async def index_page() -> None:
        days = dummy_days(settings.INDEX_HABIT_ITEM_COUNT)
        habit_list = get_or_create_session_habit_list(days)
        index_page_ui(habit_list)

    screen.open("/", timeout=60)
    screen.should_contain("Demo")
