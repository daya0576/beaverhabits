from nicegui import ui

from beaverhabits import const, views
from beaverhabits.app.auth import user_deletion
from beaverhabits.app.db import User
from beaverhabits.frontend.components import compat_card, habit_backup_dialog
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.storage import HabitList
from beaverhabits.utils import send_email


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


def delete_account(habit_list: HabitList, user: User):

    ui.label(f"Permanently delete account {user.email}.")
    btn = ui.button("Delete", icon="sym_r_delete", color=None)
    btn.props("outline")

    with ui.dialog() as dialog, ui.card():
        ui.label(
            f"⚠️ Warning: Account {user.email} will be permanently deleted. This action cannot be reversed."
        )
        with ui.row():
            ui.button("Yes", on_click=lambda: dialog.submit("Yes"))
            ui.button("No", on_click=lambda: dialog.submit("No"))

    export_json = lambda: views.export_user_habit_list(habit_list, user.email)

    async def show():
        result = await dialog
        if not result:
            return

        await export_json()

        await user_deletion(user)

        ui.navigate.reload()

    btn.on_click(show)


async def export_page(habit_list: HabitList, user: User):
    ui.colors(primary=const.DARK_COLOR)

    with layout(title="Export"):
        with ui.column().classes("w-80"):
            with compat_card().classes("w-full"):
                export_panel(habit_list, user)
            with compat_card().classes("w-full"):
                backup_panel(habit_list)
            with compat_card().classes("w-full"):
                delete_account(habit_list, user)
