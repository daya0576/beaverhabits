import datetime
from nicegui.testing import Screen

from beaverhabits.frontend.add_page import add_page_ui
from beaverhabits.frontend.habit_page import habit_page_ui
from beaverhabits.frontend.index_page import index_page_ui
from beaverhabits.views import (
    dummy_habit_list,
)

# Test cases:
# https://github.com/zauberzeug/nicegui/tree/main/tests


def dummy_today():
    return datetime.date(2024, 5, 1)


def dummy_days(count):
    today = dummy_today()
    return [today - datetime.timedelta(days=i) for i in reversed(range(count))]


def test_index_page(screen: Screen) -> None:
    days = dummy_days(7)
    habits = dummy_habit_list(days)

    index_page_ui(days, habits)

    screen.open("/", timeout=60)
    screen.should_contain("Habits")


def test_add_page(screen: Screen) -> None:
    days = dummy_days(7)
    habits = dummy_habit_list(days)

    add_page_ui(habits)

    screen.open("/", timeout=60)
    screen.should_contain("Habits")


def test_habit_detail_page(screen: Screen) -> None:
    days = dummy_days(7)
    today = days[-1]
    habits = dummy_habit_list(days)
    habit = habits.habits[0]

    habit_page_ui(today, habit)

    screen.open("/", timeout=60)
    screen.should_contain("Order pizz")
