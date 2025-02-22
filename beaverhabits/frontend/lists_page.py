from nicegui import ui

from beaverhabits import views
from beaverhabits.frontend.components import grid
from beaverhabits.frontend.layout import layout
from beaverhabits.sql.models import HabitList
from beaverhabits.app.crud import create_list, update_list, get_user_lists
from beaverhabits.app.db import User


@ui.refreshable
async def lists_ui(lists: list[HabitList], user: User | None = None):
    """Lists UI component."""
    with ui.column().classes("w-full gap-4"):
        # Add new list form
        with ui.card().classes("w-full"):
            with grid(columns=8):
                new_list_input = ui.input("New list").classes("col-span-6")
                
                async def add_list():
                    if not new_list_input.value:
                        ui.notify("List name cannot be empty", color="negative")
                        return
                    try:
                        await create_list(user, new_list_input.value)
                        new_list_input.set_value("")
                        ui.notify("List added successfully", color="positive")
                        ui.navigate.to("/gui/lists")  # Reload the page with fresh data
                    except Exception as e:
                        ui.notify(f"Failed to add list: {str(e)}", color="negative")
                
                ui.button("Add", on_click=add_list).classes("col-span-2")

        # Existing lists
        active_lists = [l for l in lists if not l.deleted]
        active_lists.sort(key=lambda l: l.order)
        
        for list_item in active_lists:
            with ui.card().classes("w-full"):
                with grid(columns=8):
                    # Use a unique variable name for each list's input
                    edit_input = ui.input(value=list_item.name).classes("col-span-5")
                    
                    async def update_list_name(list_id: int, input_element: ui.input):
                        if not input_element.value:
                            ui.notify("List name cannot be empty", color="negative")
                            return
                        try:
                            await update_list(list_id, user.id, name=input_element.value)
                            ui.notify("List updated successfully", color="positive")
                            ui.navigate.to("/gui/lists")  # Reload the page with fresh data
                        except Exception as e:
                            ui.notify(f"Failed to update list: {str(e)}", color="negative")
                    
                    async def delete_list_item(list_id: int):
                        try:
                            await update_list(list_id, user.id, deleted=True)
                            ui.notify("List deleted successfully", color="positive")
                            ui.navigate.to("/gui/lists")  # Reload the page with fresh data
                        except Exception as e:
                            ui.notify(f"Failed to delete list: {str(e)}", color="negative")
                    
                    ui.button(
                        "Save", 
                        on_click=lambda l=list_item, i=edit_input: update_list_name(l.id, i)
                    ).classes("col-span-1")
                    ui.button(
                        "Delete", 
                        on_click=lambda l=list_item: delete_list_item(l.id)
                    ).classes("col-span-2")


async def lists_page_ui(lists: list[HabitList], user: User | None = None):
    """Lists management page."""
    async with layout("Lists", user=user):
        await lists_ui(lists, user)
