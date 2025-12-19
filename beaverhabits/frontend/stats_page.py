import calendar
import datetime

from nicegui import ui

from beaverhabits.frontend.components import (
    CalendarHeatmap,
    habit_heat_map,
    redirect,
)
from beaverhabits.frontend.habit_page import card, card_title
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.meta import get_habit_heatmap_path
from beaverhabits.storage.storage import Habit, HabitList, HabitListBuilder, HabitStatus


def streak_card(habit: Habit, today: datetime.date, weeks: int):
    target = get_habit_heatmap_path(habit)
    with card(width=None):
        card_title(habit.name, target)
        ui.space().classes("h-1")
        habit_calendar = CalendarHeatmap.build(today, weeks, calendar.MONDAY)
        habit_heat_map(habit, habit_calendar)


@ui.refreshable
def stats_page_ui(today: datetime.date, habits: HabitList, weeks: int = 15):
    active_habits = HabitListBuilder(habits).status(HabitStatus.ACTIVE).build()

    with layout(habit_list=habits, page_ui=stats_page_ui):
        if not active_habits:
            redirect("/add")

        for habit in active_habits:
            streak_card(habit, today, weeks)
