from nicegui import ui

from beaverhabits import views
from beaverhabits.app.db import User
from beaverhabits.frontend import icons
from beaverhabits.frontend.components import habit_backup_dialog
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList


def compat_card():
    return ui.card().classes("no-shadow")


def backup_panel(habit_list: HabitList):
    backup = lambda: habit_backup_dialog(habit_list).open()

    ui.label("Backup your habits to JSON daily at midnight.")
    btn = ui.button("Backup", icon=icons.BACKUP).on("click", backup)
    btn.props('outline color="white"')


def export_panel(habit_list: HabitList, user: User):
    export_json = lambda: views.export_user_habit_list(habit_list, user.email)

    ui.label(
        "Export to JSON for a nice way to share and re-import your habits anytime."
    )
    btn = ui.button("Export JSON", icon=icons.DOWNLOAD).on("click", export_json)
    btn.props('outline color="white"')


async def export_page(habit_list: HabitList, user: User):
    # await views.export_user_habit_list(habit_list, user.email)
    with layout(title="Export"):
        with ui.column().classes("w-80"):
            with compat_card():
                export_panel(habit_list, user)
            with compat_card():
                backup_panel(habit_list)
