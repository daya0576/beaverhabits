import calendar
import datetime
from contextlib import contextmanager

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend import javascript
from beaverhabits.frontend.components import (
    CalendarHeatmap,
    HabitDateInput,
    habit_heat_map,
    habit_history,
    habit_notes,
    habit_streak,
    link,
)
from beaverhabits.frontend.css import (
    CALENDAR_CSS,
    CHECK_BOX_CSS,
    EXPANSION_CSS,
    HIDE_TIMELINE_TITLE,
    MARKDOWN_CSS,
)
from beaverhabits.frontend.layout import layout, redirect
from beaverhabits.storage.meta import get_habit_heatmap_path
from beaverhabits.storage.storage import EVERY_DAY, Habit

WEEKS_TO_DISPLAY = 15


def card_title(title: str, target: str):
    return link(title, target).classes("text-base flex justify-center")


@contextmanager
def grid(classes: str = ""):
    with ui.element("div").classes(f"grid grid-cols-1 gap-2 h-fit {classes}") as grid:
        yield grid


@contextmanager
def card(link: str | None = None, padding: float = 3):
    with ui.card().classes("gap-0 no-shadow items-center") as card:
        card.classes(f"p-{padding}")
        card.classes("w-full break-inside-avoid h-fit")
        card.style("max-width: 350px")
        if link:
            card.classes("cursor-pointer")
            card.on("click", lambda: redirect(link))

        yield card


@ui.refreshable
def habit_page(today: datetime.date, habit: Habit):
    target = get_habit_heatmap_path(habit)

    with ui.column().classes("gap-y-2"):
        with card():
            HabitDateInput(
                today, habit, refreshs=[habit_heat_map.refresh, habit_history.refresh]
            )

        with card():
            card_title("Last 3 Months", target)
            ui.space().classes("h-1")
            habit_calendar = CalendarHeatmap.build(
                today, WEEKS_TO_DISPLAY, calendar.MONDAY
            )
            habit_heat_map(habit, habit_calendar, refresh=habit_page.refresh)

        with card():
            card_title("Last Year", target)
            habit_history(today, habit)

        with card(padding=2):
            card_title("Notes", "#").tooltip("Press and hold to add notes/descriptions")
            habit_notes(habit)

        if (
            habit.period and habit.period != EVERY_DAY
        ) or settings.HABIT_SHOW_EVERY_DAY_STREAKS:
            with card():
                card_title("Best Streaks", target)
                habit_streak(today, habit)

        with card(target, padding=0.5):
            ui.icon("more_horiz", size="1.5em")


def habit_page_ui(today: datetime.date, habit: Habit):
    CUSTOM_CSS = [
        CHECK_BOX_CSS,
        CALENDAR_CSS,
        EXPANSION_CSS,
        HIDE_TIMELINE_TITLE,
        MARKDOWN_CSS,
    ]
    ui.add_css("\n".join(CUSTOM_CSS))

    with layout(title=habit.name, habit=habit):
        habit_page(today, habit)
