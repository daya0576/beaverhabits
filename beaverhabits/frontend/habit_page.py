import calendar
from contextlib import contextmanager
import datetime
from nicegui import ui
from beaverhabits.frontend import icons
from beaverhabits.frontend.components import HabitCalendar, HabitDateInput
from beaverhabits.frontend.css import CHECK_BOX_CSS
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import Habit


@contextmanager
def card():
    with ui.card().classes("px-3 py-3 gap-0 shadow-none items-center") as card:
        card.style("width: 350px")
        yield


def month_records(habit: Habit):
    ticked_days = set(habit.ticked_days)

    today = datetime.date.today()
    habit_calendar = HabitCalendar.build(today, weeks=15, firstweekday=calendar.MONDAY)

    # Headers
    with ui.row(wrap=False).classes("gap-0"):
        for header in habit_calendar.headers:
            header_lable = ui.label(header).classes("text-gray-300 text-center")
            header_lable.style("width: 20px; line-height: 18px; font-size: 9px;")
        ui.label().style("width: 22px;")

    # Day matrix
    for i, weekday_days in enumerate(habit_calendar.data):
        with ui.row(wrap=False).classes("gap-0"):
            for day in weekday_days:
                if day <= habit_calendar.month_last_day:
                    icon = icons.SQUARE_UNCHECKED.format(text=day.day)
                    checkbox = ui.checkbox().classes("inline-block")
                    checkbox = checkbox.props(f'dense unchecked-icon="{icon}"')
                else:
                    ui.label().style("width: 20px; height: 20px;")

            week_day_abbr_label = ui.label(habit_calendar.week_days[i])
            week_day_abbr_label.classes("indent-1.5 text-gray-300")
            week_day_abbr_label.style("width: 22px; line-height: 20px; font-size: 9px;")


def habit_page_ui(habit: Habit):
    ui.add_css(CHECK_BOX_CSS)

    with layout(title=habit.name):
        with ui.column():
            with card():
                ui.label("Calendar").classes("text-base")
                HabitDateInput(habit)

            with card():
                ui.label("Last 3 Months").classes("text-base")
                ui.label().style("height: 8px")
                month_records(habit)
