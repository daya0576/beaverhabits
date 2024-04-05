from nicegui import json
from nicegui.testing import Screen
from beaverhabits.demo import dummy_habit_list

from beaverhabits.gui import index_page


def test_markdown_message(screen: Screen) -> None:
    index_page()

    screen.open("/")
    screen.should_contain("Try running")


def test_session_storage():
    habit_list = dummy_habit_list()
    json.dumps(habit_list)

    habit_list.habits = sorted(habit_list.habits, key=lambda x: x.priority)
