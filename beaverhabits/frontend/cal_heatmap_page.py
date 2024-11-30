import datetime

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.frontend.components import (
    CalendarHeatmap,
    habit_heat_map,
    menu_header,
)
from beaverhabits.frontend.css import CHECK_BOX_CSS
from beaverhabits.storage.meta import get_habit_page_path
from beaverhabits.storage.storage import Habit

WEEKS_TO_DISPLAY = 53


def heatmap_page(today: datetime.date, habit: Habit):
    ui.add_css(CHECK_BOX_CSS)

    ticked_data = {x: True for x in habit.ticked_days}
    start_date = min(ticked_data.keys()) if ticked_data else today

    root_path = get_habit_page_path(habit)
    title = habit.name
    menu_header(title, target=root_path)

    with ui.column():
        while today > start_date:
            with ui.card().classes("p-3 gap-0 no-shadow items-center"):
                ui.label(today.strftime("%Y")).classes("text-base")

                habit_calendar = CalendarHeatmap.build(
                    today, WEEKS_TO_DISPLAY, settings.FIRST_DAY_OF_WEEK
                )
                habit_heat_map(
                    habit, habit_calendar, ticked_data=ticked_data, readonly=True
                )

                today -= datetime.timedelta(days=7 * WEEKS_TO_DISPLAY)
