import calendar
import datetime
from contextlib import contextmanager

from nicegui import ui

from beaverhabits.frontend.components import (
    CalendarHeatmap,
    HabitDateInput,
    habit_heat_map,
    habit_history,
    link,
)
from beaverhabits.frontend.css import CALENDAR_CSS, CHECK_BOX_CSS
from beaverhabits.frontend.layout import layout, redirect
from beaverhabits.storage.meta import get_habit_heatmap_path
from beaverhabits.storage.storage import Habit

WEEKS_TO_DISPLAY = 15


@contextmanager
def card(link: str | None = None):
    with ui.card().classes("p-3 gap-0 no-shadow items-center") as card:
        card.classes("w-full")
        card.style("max-width: 350px")
        if link:
            card.classes("cursor-pointer")
            card.on("click", lambda: redirect(link))
        yield


def habit_page(today: datetime.date, habit: Habit):
    with ui.column().classes("gap-y-3"):
        ticked_data = {x: True for x in habit.ticked_days}
        habit_calendar = CalendarHeatmap.build(today, WEEKS_TO_DISPLAY, calendar.MONDAY)

        with card():
            HabitDateInput(today, habit, ticked_data)

        with card():
            link("Last 3 Months", get_habit_heatmap_path(habit)).classes(
                "text-base flex justify-center"
            )
            habit_heat_map(habit, habit_calendar, ticked_data=ticked_data)

        with card():
            ui.label("History").classes("text-base flex justify-center")
            habit_history(today, list(ticked_data.keys()))


def habit_page_ui(today: datetime.date, habit: Habit):
    ui.add_css(CHECK_BOX_CSS)
    ui.add_css(CALENDAR_CSS)

    with layout(title=habit.name):
        # with ui.row().classes("gap-y-3"):
        habit_page(today, habit)
