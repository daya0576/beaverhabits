from nicegui import ui

from beaverhabits import const, views
from beaverhabits.app.db import User
from beaverhabits.frontend.components import compat_card, habit_backup_dialog
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList


def backup_panel(habit_list: HabitList):
    backup = lambda: habit_backup_dialog(habit_list).open()

    ui.label("Backup your habits to JSON daily at midnight.")
    btn = ui.button("Backup", icon="sym_r_backup", color=None)
    btn.on("click", backup)
    btn.props("outline")


def export_panel(habit_list: HabitList, user: User):
    export_json = lambda: views.export_user_habit_list(habit_list, user.email)

    ui.label(
        "Export to JSON for a nice way to share and re-import your habits anytime."
    )
    btn = ui.button("Export JSON", icon="sym_r_download", color=None)
    btn.on("click", export_json)
    btn.props("outline")


async def export_page(habit_list: HabitList, user: User):
    ui.colors(primary=const.DARK_COLOR)

    with layout(title="Export"):
        with ui.column().classes("w-80"):
            with compat_card().classes("w-full"):
                export_panel(habit_list, user)
            with compat_card().classes("w-full"):
                backup_panel(habit_list)
