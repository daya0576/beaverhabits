import calendar
import datetime
from contextlib import contextmanager

from nicegui import ui

from beaverhabits.frontend.components import (
    CalendarHeatmap,
    HabitDateInput,
    habit_heat_map,
    habit_history,
    habit_notes,
    link,
)
from beaverhabits.frontend.css import (
    CALENDAR_CSS,
    CHECK_BOX_CSS,
    EXPANSION_CSS,
    HIDE_TIMELINE_TITLE,
)
from beaverhabits.frontend.layout import layout, redirect
from beaverhabits.storage.meta import get_habit_heatmap_path
from beaverhabits.storage.storage import Habit

WEEKS_TO_DISPLAY = 15


def card_title(title: str, target: str):
    return link(title, target).classes("text-base flex justify-center")


@contextmanager
def card(link: str | None = None, padding: float = 3):
    with ui.card().classes("gap-0 no-shadow items-center") as card:
        card.classes(f"p-{padding}")
        card.classes("w-full break-inside-avoid mb-2")
        card.style("max-width: 350px")
        if link:
            card.classes("cursor-pointer")
            card.on("click", lambda: redirect(link))

        yield card


@ui.refreshable
def habit_page(today: datetime.date, habit: Habit):
    with ui.element("div").classes("columns-1 lg:columns-2 w-full gap-2"):
        habit_calendar = CalendarHeatmap.build(today, WEEKS_TO_DISPLAY, calendar.MONDAY)
        target = get_habit_heatmap_path(habit)

        with card():
            HabitDateInput(today, habit)

        with card():
            card_title("Last 3 Months", target)
            ui.space().classes("h-2")
            habit_heat_map(habit, habit_calendar)

        with card():
            card_title("History", target)
            ui.space().classes("h-1")
            habit_history(today, habit.ticked_days)

        with card(padding=2):
            card_title("Notes", "#").tooltip("Press and hold to add notes/descriptions")
            habit_notes(habit)

        with card(target, padding=0.5):
            ui.icon("more_horiz", size="1.5em")


def habit_page_ui(today: datetime.date, habit: Habit):
    ui.add_css(CHECK_BOX_CSS)
    ui.add_css(CALENDAR_CSS)
    ui.add_css(EXPANSION_CSS)
    ui.add_css(HIDE_TIMELINE_TITLE)

    with layout(title=habit.name):
        habit_page(today, habit)
