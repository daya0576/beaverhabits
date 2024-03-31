from nicegui import ui
from beaverhabits.frontend.layout import layout

from beaverhabits.storage.storage import HabitList


@ui.refreshable
def add_ui(habit_list: HabitList):
    habit_list = habit_list
    # ui.linear_progress(
    #     sum(item.done for item in todos.items) / len(todos.items), show_value=False
    # )
    # with ui.row().classes("justify-center w-full"):
    #     ui.label(f"Completed: {sum(item.done for item in todos.items)}")
    #     ui.label(f"Remaining: {sum(not item.done for item in todos.items)}")
    for item in habit_list.items:
        with ui.row().classes("items-center"):
            # ui.checkbox(value=item.done, on_change=todo_ui.refresh).bind_value(
            #     item, "done"
            # )
            ui.input(value=item.name).classes("flex-grow").bind_value(item, "name")
            ui.button(
                on_click=lambda item=item: habit_list.remove(item), icon="delete"
            ).props("flat fab-mini color=grey")


def add_page_ui(habit_list: HabitList, root_path: str):
    with layout(root_path):
        with ui.card().classes("w-80 items-stretch"):
            add_ui(habit_list)
            add_input = ui.input("New item").classes("mx-12")
            add_input.on(
                "keydown.enter",
                lambda: (habit_list.add(add_input.value), add_input.set_value("")),
            )
