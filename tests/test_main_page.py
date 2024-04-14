from nicegui.testing import Screen
from beaverhabits.main import *

# Test cases:
# https://github.com/zauberzeug/nicegui/tree/main/tests


def test_hello():
    assert "Hello" == "Hello"


def test_index_page(screen: Screen) -> None:
    screen.open("/demo", timeout=10)
    screen.should_contain("Demo")

    screen.open("/demo/add", timeout=10)
    screen.should_contain("Demo")
