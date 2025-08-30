import datetime
import os
from collections import OrderedDict
from typing import List

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.core.completions import get_habit_date_completion
from beaverhabits.frontend import javascript, textarea
from beaverhabits.frontend.components import (
    HabitCheckBox,
    IndexStreakBadge,
    IndexTotalBadge,
    TagManager,
    habit_name_menu,
    habits_by_tags,
    tag_filter_component,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import (
    CheckedState,
    Habit,
    HabitList,
    HabitListBuilder,
    HabitStatus,
)

NAME_COLS, DATE_COLS = settings.INDEX_HABIT_NAME_COLUMNS, 2
COUNT_BADGE_COLS = 2 if settings.INDEX_SHOW_HABIT_COUNT else 0
COUNT_BADGE_COLS += 2 if settings.INDEX_SHOW_HABIT_STREAK else 0
LEFT_CLASSES, RIGHT_CLASSES = (
    # grid 5
    f"col-span-{NAME_COLS} truncate max-w-[{24 * NAME_COLS}px]",
    # grid 2 2 2 2 2
    f"col-span-{DATE_COLS} px-1 place-self-center",
)
COMPAT_CLASSES = "pl-4 pr-0 py-0 dark:shadow-none"

# Sticky date row for long habit list
STICKY_STYLES = "position: sticky; top: 0; z-index: 1;"


def grid(columns, rows):
    g = ui.grid(columns=columns, rows=rows)
    g.classes("w-full gap-0 items-center")
    return g


def week_headers(days: list[datetime.date]):
    for day in days:
        yield day.strftime("%a")
    if settings.INDEX_SHOW_HABIT_STREAK:
        yield "Stk"
    if settings.INDEX_SHOW_HABIT_COUNT:
        yield "Sum"


def day_headers(days: list[datetime.date]):
    for day in days:
        yield day.strftime("%d")
    if settings.INDEX_SHOW_HABIT_STREAK:
        yield "*"
    if settings.INDEX_SHOW_HABIT_COUNT:
        yield "#"


def habit_row(habit: Habit, tag: str, days: list[datetime.date]):
    name = habit_name_menu(habit, index_page_ui.refresh)
    name.classes(LEFT_CLASSES)
    name.props(f'role="heading" aria-level="2" aria-label="{habit.name}"')

    today = max(days)
    status_map = get_habit_date_completion(habit, min(days), today)
    for day in days:
        status = status_map.get(day, CheckedState.UNKNOWN)
        checkbox = HabitCheckBox(
            status, habit, today, day, refresh=habit_list_ui.refresh
        )
        checkbox.classes(RIGHT_CLASSES)
        # checkbox.classes("theme-icon-lazy invisible")

    if settings.INDEX_SHOW_HABIT_STREAK:
        IndexStreakBadge(today, habit).classes(RIGHT_CLASSES)

    if settings.INDEX_SHOW_HABIT_COUNT:
        IndexTotalBadge(today, habit).classes(RIGHT_CLASSES)


@ui.refreshable
def habit_list_ui(days: list[datetime.date], active_habits: List[Habit]):
    # Total cloumn for each row
    columns = NAME_COLS + len(days) * DATE_COLS + COUNT_BADGE_COLS

    with ui.column().classes("gap-1.5"):
        # Date Headers
        with grid(columns, 2).classes(COMPAT_CLASSES).style(STICKY_STYLES) as g:
            g.props('aria-hidden="true"').classes("theme-header-date")
            for it in (week_headers(days), day_headers(days)):
                ui.label("").classes(LEFT_CLASSES)
                for label in it:
                    ui.label(label).classes(RIGHT_CLASSES)

        # Habit Rows
        groups = habits_by_tags(active_habits)

        for tag, habit_list in groups.items():
            if not habit_list:
                continue

            for habit in habit_list:
                with ui.card().classes(COMPAT_CLASSES).classes("theme-card-shadow"):
                    with grid(columns, 1):
                        habit_row(habit, tag, days)

            ui.space()


@ui.refreshable
def index_page_ui(days: list[datetime.date], habits: HabitList):
    active_habits = HabitListBuilder(habits).status(HabitStatus.ACTIVE).build()
    if settings.INDEX_HABIT_DATE_REVERSE:
        days = list(reversed(days))

    with layout(habit_list=habits):
        if not active_habits:
            ui.label("List is empty.").classes("mx-auto w-80")
            return
        habit_list_ui(days, active_habits)

    # placeholder to preload js cache (daily notes)
    textarea.Textarea("").classes("hidden").props('aria-hidden="true"')
    ui.input("").classes("hidden").props('aria-hidden="true"')
