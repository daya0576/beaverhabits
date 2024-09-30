import calendar
import datetime

from nicegui import ui

from beaverhabits.frontend.components import (
    CalendarHeatmap,
    habit_heat_map,
    menu_header,
)
from beaverhabits.frontend.css import CHECK_BOX_CSS
from beaverhabits.storage.meta import get_habit_page_path
from beaverhabits.storage.storage import Habit

WEEKS_TO_DISPLAY = 56


def heatmap_page(today: datetime.date, habit: Habit):
    ui.add_css(CHECK_BOX_CSS)

    ticked_data = {x: True for x in habit.ticked_days}
    habit_calendar = CalendarHeatmap.build(today, WEEKS_TO_DISPLAY, calendar.MONDAY)

    root_path = get_habit_page_path(habit)
    title = habit.name
    menu_header(title, target=root_path)

    with ui.column().classes("gap-0"):
        with ui.card().classes("p-3 gap-0 no-shadow items-center"):
            # ui.label("Last Year").classes("text-base")
            habit_heat_map(habit, habit_calendar, ticked_data=ticked_data)
