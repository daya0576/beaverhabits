from nicegui import ui

from beaverhabits.frontend.components import menu_icon_item
from beaverhabits.frontend.layout import redirect
from beaverhabits.storage.storage import HabitList, HabitOrder


def add_menu():
    add = menu_icon_item("Add", lambda: redirect("add"))
    add.props('aria-label="Add habit"')


def sort_menu(habit_list: HabitList):
    with menu_icon_item("Sort", auto_close=False):
        with ui.item_section().props("side"):
            ui.icon("keyboard_arrow_right")

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
