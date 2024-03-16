from nicegui import app, ui

from .gui import router as gui_router


@ui.page("/")
def index_page() -> None:
    ui.label("hello")


app.include_router(gui_router)

ui.run(storage_secret="THIS_NEEDS_TO_BE_CHANGED", dark=True)
