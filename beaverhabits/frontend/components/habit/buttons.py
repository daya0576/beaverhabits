from typing import Callable
from nicegui import ui, events

from beaverhabits.frontend import icons
from beaverhabits.logging import logger
from beaverhabits.storage.storage import Habit, HabitList, HabitStatus

class HabitEditButton(ui.button):
    def __init__(self, habit: Habit) -> None:
        super().__init__(on_click=self._async_task, icon="edit_square")
        self.habit = habit
        self.props("flat fab-mini color=grey-8")

    async def _async_task(self):
        pass

class HabitDeleteButton(ui.button):
    def __init__(self, habit: Habit, habit_list: HabitList, refresh: Callable) -> None:
        icon = icons.DELETE if habit.status == HabitStatus.ACTIVE else icons.DELETE_F
        super().__init__(on_click=self._async_task, icon=icon)
        self.habit = habit
        self.habit_list = habit_list
        self.refresh = refresh
        self.props("flat fab-mini color=grey-9")

        # Double confirm dialog to delete habit
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Are you sure to delete habit: {habit.name}?")
            with ui.row():
                ui.button("Yes", on_click=lambda: dialog.submit(True))
                ui.button("No", on_click=lambda: dialog.submit(False))
        self.dialog = dialog

    async def _async_task(self):
        if self.habit.status == HabitStatus.ACTIVE:
            self.habit.status = HabitStatus.ARCHIVED
            logger.info(f"Archive habit: {self.habit.name}")

        elif self.habit.status == HabitStatus.ARCHIVED:
            if not await self.dialog:
                return
            self.habit.status = HabitStatus.SOLF_DELETED
            logger.info(f"Soft delete habit: {self.habit.name}")

        self.refresh()

class HabitAddButton:
    def __init__(self, habit_list: HabitList, refresh: Callable, list_options: list[dict]) -> None:
        self.habit_list = habit_list
        self.refresh = refresh
        
        with ui.column().classes("w-full gap-2"):
            with ui.row().classes("w-full items-center gap-2"):
                self.name_input = ui.input("New habit name").props('dense outlined')
                self.name_input.classes("flex-grow")
                
                self.goal_input = ui.number(min=0, max=7).props('dense outlined')
                self.goal_input.style("width: 120px")
                
                # Create name-to-id mapping for list selector
                self.name_to_id = {"No List": None}
                self.name_to_id.update({opt["label"]: opt["value"] for opt in list_options[1:]})
                
                # Use just the names as options
                options = list(self.name_to_id.keys())
                
                self.list_select = ui.select(
                    options=options,
                    value="No List",
                ).props('dense outlined options-dense')
                self.list_select.style("width: 150px")
            
            with ui.row().classes("w-full justify-end"):
                ui.button("Add Habit", on_click=self._async_task).props("unelevated")
            
        # Keep enter key functionality
        self.name_input.on("keydown.enter", self._async_task)
        self.goal_input.on("keydown.enter", self._async_task)

    async def _async_task(self):
        if not self.name_input.value:
            return
        await self.habit_list.add(self.name_input.value)
        # Set weekly goal and list after habit is created
        habits = self.habit_list.habits
        if habits:
            habits[-1].weekly_goal = self.goal_input.value or 0  # Default to 0 if empty
            habits[-1].list_id = self.name_to_id[self.list_select.value]
            logger.info(f"Set weekly goal to {habits[-1].weekly_goal}")
            logger.info(f"Set list to {habits[-1].list_id}")
        logger.info(f"Added new habit: {self.name_input.value}")
        self.refresh()
        self.name_input.set_value("")
        self.goal_input.set_value(None)
        self.list_select.set_value(None)
