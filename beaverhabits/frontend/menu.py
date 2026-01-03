import datetime
import enum

from nicegui import app, ui

from beaverhabits import utils
from beaverhabits.frontend.components import menu_icon_item
from beaverhabits.frontend.layout import redirect
from beaverhabits.storage.storage import HabitList, HabitOrder

STATS_START_DATE = "stats_start_date"
STATS_END_DATE = "stats_end_date"


def add_menu():
    add = menu_icon_item("Add", lambda: redirect("add"))
    add.props('aria-label="Add habit"')


def sort_menu(habit_list: HabitList):
    def set_order(order: HabitOrder):
        habit_list.order_by = order
        ui.navigate.reload()

    def set_custom():
        habit_list.order_by = HabitOrder.MANUALLY
        redirect("order")

    with ui.menu().props('anchor="top end" self="top start" auto-close'):
        name = menu_icon_item("by Name", lambda: set_order(HabitOrder.NAME))
        if habit_list.order_by == HabitOrder.NAME:
            name.props("active")

        cat = menu_icon_item("by Category", lambda: set_order(HabitOrder.CATEGORY))
        if habit_list.order_by == HabitOrder.CATEGORY:
            cat.props("active")

        manually = menu_icon_item("Manually", set_custom)
        if habit_list.order_by == HabitOrder.MANUALLY:
            manually.props("active")


def get_stats_date_range() -> tuple[datetime.date | None, datetime.date | None]:
    start_str = app.storage.user.get(STATS_START_DATE)
    end_str = app.storage.user.get(STATS_END_DATE)

    start_date = datetime.date.fromisoformat(start_str) if start_str else None
    end_date = datetime.date.fromisoformat(end_str) if end_str else None

    return start_date, end_date


def set_stats_date_range(start_date: datetime.date, end_date: datetime.date):
    app.storage.user[STATS_START_DATE] = start_date.isoformat()
    app.storage.user[STATS_END_DATE] = end_date.isoformat()


def stats_date_pick_menu():
    def reload_page(start_date: datetime.date, end_date: datetime.date):
        set_stats_date_range(start_date, end_date)
        ui.navigate.reload()

    today = utils.get_user_today_date_sync()
    with ui.menu().props('anchor="top end" self="top start" auto-close'):
        # Last 3 months
        start_3m = today - datetime.timedelta(weeks=15)
        menu_icon_item("Last 3 Months", lambda: reload_page(start_3m, today))
        # Last 6 months
        start_6m = today - datetime.timedelta(weeks=26)
        menu_icon_item("Last 6 Months", lambda: reload_page(start_6m, today))
        # Last year (52 weeks)
        start_1y = today - datetime.timedelta(weeks=53)
        menu_icon_item("Last Year", lambda: reload_page(start_1y, today))

        # Add year-wise options from current year down to 2024
        if (current_year := today.year) < 2024:
            return
        ui.separator()
        for year in range(current_year, 2023, -1):
            year_start = datetime.date(year, 1, 1)
            year_end = datetime.date(year, 12, 31)
            menu_icon_item(
                str(year),
                lambda s=year_start, e=year_end: reload_page(s, e),
            )
