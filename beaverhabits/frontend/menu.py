import enum

from nicegui import ui

from beaverhabits.frontend.components import menu_icon_item
from beaverhabits.frontend.layout import redirect
from beaverhabits.storage.storage import HabitList, HabitOrder


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


class StatsPeriod(enum.Enum):
    THREE_MONTHS = 15
    SIX_MONTHS = 25
    ONE_YEAR = 42


def date_pick_menu(page_ui: ui.refreshable):
    def refresh_page(period: StatsPeriod):
        page_ui.refresh(weeks=period.value)

    with ui.menu().props('anchor="top end" self="top start" auto-close'):
        menu_icon_item("3 Months", lambda: refresh_page(StatsPeriod.THREE_MONTHS))
        menu_icon_item("6 Months", lambda: refresh_page(StatsPeriod.SIX_MONTHS))
        menu_icon_item("1 Year", lambda: refresh_page(StatsPeriod.ONE_YEAR))
