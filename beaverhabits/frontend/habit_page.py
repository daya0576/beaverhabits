import calendar
import datetime
from contextlib import contextmanager

from nicegui import ui

from beaverhabits.frontend.components import (
    CalendarHeatmap,
    HabitDateInput,
    habit_heat_map,
)
from beaverhabits.frontend.css import CALENDAR_CSS, CHECK_BOX_CSS
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import Habit

WEEKS_TO_DISPLAY = 15


@contextmanager
def card():
    with ui.card().classes("p-3 gap-0 no-shadow items-center") as card:
        card.classes("w-full")
        card.style("max-width: 350px")
        yield


def habit_page(habit: Habit):
    today = datetime.date.today()
    ticked_data = {x: True for x in habit.ticked_days}
    habit_calendar = CalendarHeatmap.build(today, WEEKS_TO_DISPLAY, calendar.MONDAY)

    with card():
        # ui.label("Calendar").classes("text-base")
        today = datetime.date.today()
        HabitDateInput(today, habit, ticked_data)

    with ui.dialog() as dialog, ui.card():
        ui.label("Hello world!")
        ui.button("Close", on_click=dialog.close)
    with card():
        ui.label("Last 3 Months").classes("text-base")
        habit_heat_map(habit, habit_calendar, ticked_data=ticked_data)


def habit_page_ui(habit: Habit):
    ui.add_css(CHECK_BOX_CSS)
    ui.add_css(CALENDAR_CSS)

    with layout(title=habit.name):
        habit_page(habit)
