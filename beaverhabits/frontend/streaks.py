import datetime

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend.components import (
    CalendarHeatmap,
    habit_heat_map,
    habit_history,
    habit_notes,
)
from beaverhabits.frontend.css import CHECK_BOX_CSS, NOTE_CSS
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import Habit

WEEKS_TO_DISPLAY = 53


def compat_card():
    card = ui.card().classes("p-3 gap-0 no-shadow items-center")
    card.classes("w-[1106px] break-inside-avoid h-fit")
    return card


def streaks(today: datetime.date, habit: Habit):
    ticked_data = {x: True for x in habit.ticked_days}
    start_date = min(ticked_data.keys()) if ticked_data else today

    while today > start_date:
        with compat_card():
            ui.label(today.strftime("%Y")).classes("text-lg")
            ui.space().classes("h-1")
            habit_calendar = CalendarHeatmap.build(
                today, WEEKS_TO_DISPLAY, settings.FIRST_DAY_OF_WEEK
            )
            habit_heat_map(habit, habit_calendar, readonly=True)

            today -= datetime.timedelta(days=7 * WEEKS_TO_DISPLAY)


def history(today: datetime.date, habit: Habit):
    with compat_card():
        ui.label("History").classes("text-lg")
        habit_history(today, habit, total_months=48)


def notes(habit: Habit, limit: int = 100):
    with compat_card():
        ui.label("Notes").classes("text-lg")
        habit_notes(habit, limit=limit)


def heatmap_page(today: datetime.date, habit: Habit):
    ui.add_css(CHECK_BOX_CSS)
    ui.add_css(NOTE_CSS)

    # Header
    with layout(title=habit.name):
        # Main body
        history(today, habit)
        streaks(today, habit)
        notes(habit, limit=100)
