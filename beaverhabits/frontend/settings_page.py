from nicegui import ui

from beaverhabits import views
from beaverhabits.app.db import User
from beaverhabits.frontend.layout import layout
from beaverhabits.utils import set_user_dark_mode

EDIT_ME = """\
/* Edit this CSS to customize theme */
/* body {
    background-color: #ddd !important;
} */
"""


async def settings_page(user: User):
    configs = await views.get_user_configs(user)

    async def update_custom_css(e):
        await views.update_custom_css(user, e.value)
        await views.apply_theme_style()

    def toggle_dark_mode(value: bool):
        set_user_dark_mode(value)
        if value:
            ui.dark_mode().enable()
        else:
            ui.dark_mode().disable()

    with layout(title="Settings"):
        with ui.column().classes("w-[600px]"):
            # ui.label("Darkmode").classes("text-lg font-bold")
            # with ui.row():
            #     ui.button("Dark", on_click=lambda: toggle_dark_mode(True))
            #     ui.button("Light", on_click=lambda: toggle_dark_mode(False))

            ui.label("Custom CSS").classes("text-lg font-bold")
            editor = ui.codemirror(
                configs.custom_css or EDIT_ME, language="CSS", theme="githubDark"
            ).classes("h-96")
            editor.on_value_change(update_custom_css)
