import calendar
import datetime
from contextlib import contextmanager

from nicegui import ui

from beaverhabits.frontend.components import (
    CalendarHeatmap,
    HabitDateInput,
    habit_heat_map,
    link,
)
from beaverhabits.frontend.css import CALENDAR_CSS, CHECK_BOX_CSS
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.meta import get_habit_heatmap_path
from beaverhabits.storage.storage import Habit

WEEKS_TO_DISPLAY = 15


@contextmanager
def card():
    with ui.card().classes("p-3 gap-0 no-shadow items-center") as card:
        card.classes("w-full")
        card.style("max-width: 350px")
        yield


def habit_page(today: datetime.date, habit: Habit):
    ticked_data = {x: True for x in habit.ticked_days}
    habit_calendar = CalendarHeatmap.build(today, WEEKS_TO_DISPLAY, calendar.MONDAY)

    with card():
        # ui.label("Calendar").classes("text-base")
        HabitDateInput(today, habit, ticked_data)

    with card():
        link("Last 3 Months", get_habit_heatmap_path(habit)).classes("text-base")
        habit_heat_map(habit, habit_calendar, ticked_data=ticked_data)

    with card():
        link("Total", get_habit_heatmap_path(habit)).classes("text-base")


def habit_page_ui(today: datetime.date, habit: Habit):
    ui.add_css(CHECK_BOX_CSS)
    ui.add_css(CALENDAR_CSS)

    with layout(title=habit.name):
        habit_page(today, habit)
