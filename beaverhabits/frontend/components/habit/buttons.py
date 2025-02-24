from typing import Callable, Optional, TYPE_CHECKING

from nicegui import ui

from beaverhabits.sql.models import Habit, HabitList
from beaverhabits.app.crud import update_habit, create_habit, get_user_habits, get_user_lists
from beaverhabits.frontend import icons
from beaverhabits.app.db import User

if TYPE_CHECKING:
    from beaverhabits.frontend.components.habit.inputs import WeeklyGoalInput, HabitNameInput

class HabitEditButton(ui.button):
    def __init__(self, habit: Habit, refresh: Callable) -> None:
        super().__init__()
        self.habit = habit
        self.refresh = refresh
        self.props("flat fab-mini")
        self.props(f'icon="{icons.EDIT}"')

        self.on("click", self._async_task)

    async def _async_task(self, e):
        with ui.dialog() as dialog, ui.card().props("flat"):
            with ui.column().classes("gap-0 w-full"):
                t = ui.input(
                    label="Name",
                    value=self.habit.name,
                    validation={"Required": lambda value: bool(value.strip())},
                )
                t.classes("w-full")

                with ui.row():
                    ui.button("Save", on_click=lambda: dialog.submit(t.value)).props(
                        "flat"
                    )
                    ui.button("Cancel", on_click=dialog.close).props("flat")

        result = await dialog
        if result:
            await update_habit(self.habit.id, self.habit.user_id, name=result)
            self.refresh()

class HabitDeleteButton(ui.button):
    def __init__(self, habit: Habit, refresh: Callable) -> None:
        super().__init__()
        self.habit = habit
        self.refresh = refresh
        self.props("flat fab-mini")
        self.props(f'icon="{icons.DELETE}"')

        self.on("click", self._async_task)

    async def _async_task(self, e):
        with ui.dialog() as dialog, ui.card().props("flat"):
            with ui.column().classes("gap-0 w-full"):
                ui.label(f"Delete habit '{self.habit.name}'?")

                with ui.row():
                    ui.button("Yes", on_click=lambda: dialog.submit(True)).props("flat")
                    ui.button("No", on_click=dialog.close).props("flat")

        result = await dialog
        if result:
            # Delete habit
            await update_habit(self.habit.id, self.habit.user_id, deleted=True)
            # Reload the page to show the updated list
            ui.navigate.reload()

class HabitAddButton(ui.button):
    def __init__(self, user: User, list_id: Optional[int], refresh: Callable) -> None:
        super().__init__()
        self.user = user
        self.list_id = list_id
        self.refresh = refresh
        self.props("flat fab-mini")
        self.props(f'icon="{icons.ADD}"')

        self.on("click", self._async_task)

    async def _async_task(self, e):
        with ui.dialog() as dialog, ui.card().props("flat"):
            with ui.column().classes("gap-0 w-full"):
                t = ui.input(
                    label="Name",
                    validation={"Required": lambda value: bool(value.strip())},
                )
                t.classes("w-full")

                with ui.row():
                    ui.button("Add", on_click=lambda: dialog.submit(t.value)).props("flat")
                    ui.button("Cancel", on_click=dialog.close).props("flat")

        result = await dialog
        if result:
            # Create new habit
            await create_habit(self.user, result, self.list_id)
            ui.navigate.reload()  # Reload the page to show the new habit

class HabitSaveButton(ui.button):
    def __init__(self, habit: Habit, weekly_goal_input: 'WeeklyGoalInput', name_input: 'HabitNameInput', refresh: Callable) -> None:
        super().__init__("Save")
        self.habit = habit
        self.weekly_goal_input = weekly_goal_input
        self.name_input = name_input
        self.refresh = refresh
        self.props("flat")

        self.on("click", self._async_task)

    async def _async_task(self, e):
        # Save all changes to the habit
        weekly_goal = self.weekly_goal_input.get_value()
        name = self.name_input.get_value()
        await update_habit(
            self.habit.id,
            self.habit.user_id,
            name=name,
            weekly_goal=weekly_goal,
            list_id=self.habit.list_id
        )
        # Update the habit object with new values
        self.habit.weekly_goal = weekly_goal
        self.habit.name = name
        # Update the UI
        self.weekly_goal_input.value = weekly_goal
        self.name_input.value = name
        self.refresh()
