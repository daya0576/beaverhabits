import datetime
import enum

from nicegui import app, ui

from beaverhabits import utils
from beaverhabits.frontend.components import compat_card, menu_icon_item
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


def set_stats_date_range(
    start_date: datetime.date | None, end_date: datetime.date | None
):
    app.storage.user[STATS_START_DATE] = start_date.isoformat() if start_date else None
    app.storage.user[STATS_END_DATE] = end_date.isoformat() if end_date else None


def parse_date_range_str(date_range_str: str) -> tuple[datetime.date, datetime.date]:
    start_str, end_str = date_range_str.split(" - ")
    start_date = datetime.date.fromisoformat(start_str)
    end_date = datetime.date.fromisoformat(end_str)
    return start_date, end_date


def format_date_range(start_date: datetime.date, end_date: datetime.date) -> str:
    return f"{start_date.isoformat()} - {end_date.isoformat()}"


def stats_date_pick_menu():
    def reload_page(start_date: datetime.date, end_date: datetime.date):
        set_stats_date_range(start_date, end_date)
        ui.navigate.reload()

    def apply_custom_date_range():
        date_str = date_input.value
        if not date_str:
            set_stats_date_range(None, None)
            ui.navigate.reload()

        try:
            start_date, end_date = parse_date_range_str(date_str)
            assert start_date < end_date
            reload_page(start_date, end_date)
        except Exception:
            ui.notify(
                "Invalid date range. Use YYYY-MM-DD - YYYY-MM-DD",
                color="warn",
            )

    today = utils.get_user_today_date_sync()
    with ui.dialog() as dialog, ui.card():
        d_start, d_end = get_stats_date_range()
        if d_start and d_end:
            date_str = format_date_range(d_start, d_end)
        else:
            date_str = format_date_range(
                today - datetime.timedelta(weeks=26),
                today,
            )
        date_input = ui.input("Date range", value=date_str).classes("w-64")

        with ui.row():
            ui.button("Apply", on_click=apply_custom_date_range)
            ui.button("Close", on_click=dialog.close)

    with ui.menu().props('anchor="top end" self="top start" auto-close'):
        options = [
            ("Last 3 Months", 15),
            ("Last 6 Months", 26),
            ("Last Year", 53),
        ]
        for label, weeks in options:
            start_date = today - datetime.timedelta(weeks=weeks)
            menu_icon_item(
                label,
                lambda s=start_date, e=today: reload_page(s, e),
            )

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

        ui.separator()
        menu_icon_item("Custom Range", dialog.open)
