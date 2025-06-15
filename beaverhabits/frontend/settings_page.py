from nicegui import ui

from beaverhabits import const, views
from beaverhabits.app.db import User
from beaverhabits.frontend.layout import layout


async def settings_page(user: User):
    configs = await views.get_user_configs(user)

    async def update_custom_css(e):
        await views.update_custom_css(user, e.value)
        await views.apply_theme_style()

    with layout(title="Settings"):
        with ui.column().classes("w-[600px]"):
            # ui.label("Darkmode").classes("text-lg font-bold dark:text-white")
            # with ui.row():
            #     ui.button("Dark", on_click=lambda: ui.dark_mode().enable())
            #     ui.button("Light", on_click=lambda: ui.dark_mode().disable())

            ui.label("Custom CSS").classes("text-lg font-bold dark:text-white")
            editor = ui.codemirror(
                configs.custom_css or const.CSS_EDIT_ME,
                language="CSS",
                theme="githubDark",
            ).classes("h-96")
            editor.on_value_change(update_custom_css)
