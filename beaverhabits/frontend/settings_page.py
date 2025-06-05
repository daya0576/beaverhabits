from nicegui import ui

from beaverhabits import views
from beaverhabits.app.db import User
from beaverhabits.frontend.layout import layout

EDIT_ME = """\
/* Edit this CSS to customize theme */
/* body {
    background-color: #ddd;
} */
"""


async def settings_page(user: User):
    configs = await views.get_user_configs(user)

    async def update_custom_css(e):
        await views.update_custom_css(user, e.value)
        await views.apply_theme_style()

    with layout(title="Settings"):
        with ui.column().classes("w-[600px]"):
            ui.label("Darkmode").classes("text-lg font-bold")
            with ui.row():
                dark = ui.dark_mode()
                ui.button("Dark", on_click=dark.enable)
                ui.button("Light", on_click=dark.disable)

            ui.label("Custom CSS").classes("text-lg font-bold")
            editor = ui.codemirror(
                configs.custom_css or EDIT_ME, language="CSS", theme="githubDark"
            ).classes("h-96")
            editor.on_value_change(update_custom_css)
