import asyncio
import datetime
from typing import Callable

from nicegui import ui, events

from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.logging import logger
from beaverhabits.sql.models import Habit, CheckedRecord
from beaverhabits.app.crud import toggle_habit_check, get_habit_checks
from beaverhabits.frontend.components.utils import ratelimiter
from beaverhabits.frontend.components.habit.link import HabitLink
from beaverhabits.frontend.components.habit.priority import HabitPriority

DAILY_NOTE_MAX_LENGTH = 300

def habit_tick_dialog(record: CheckedRecord | None):
    text = record.text if record and hasattr(record, 'text') else ""
    with ui.dialog() as dialog, ui.card().props("flat") as card:
        dialog.props('backdrop-filter="blur(4px)"')
        card.classes("w-5/6 max-w-80")

        with ui.column().classes("gap-0 w-full"):
            t = ui.textarea(
                label="Note",
                value=text,
                validation={
                    "Too long!": lambda value: len(value) < DAILY_NOTE_MAX_LENGTH
                },
            )
            t.classes("w-full")

            with ui.row():
                ui.button("Yes", on_click=lambda: dialog.submit((True, t.value))).props(
                    "flat"
                )
                ui.button("No", on_click=lambda: dialog.submit((False, t.value))).props(
                    "flat"
                )
    return dialog

async def note_tick(habit: Habit, day: datetime.date) -> bool | None:
    # Get current record
    records = await get_habit_checks(habit.id, habit.user_id)
    record = next((r for r in records if r.day == day), None)
    
    result = await habit_tick_dialog(record)
    if result is None:
        return

    yes, text = result
    if text and len(text) > DAILY_NOTE_MAX_LENGTH:
        ui.notify("Note is too long", color="negative")
        return

    # Toggle the habit check
    record = await toggle_habit_check(habit.id, habit.user_id, day, text, True)  # Always set to checked when using notes
    
    # Get updated state from API
    from beaverhabits.frontend.components.index.habit.state import get_habit_state
    state = await get_habit_state(habit, day)
    
    # Find checkbox and update its state directly
    for element in ui.query(f'[data-habit-id="{habit.id}"]'):
        if isinstance(element, BaseHabitCheckBox):
            value = True if state.state == 'checked' else False if state.state == 'skipped' else None
            element._update_state(value)
    
    # Only use JavaScript for card sorting
    ui.run_javascript(f"window.updateHabitState('{habit.id}', {state.model_dump_json()})")
    
    return record.done if record else None

@ratelimiter(limit=30, window=30)
@ratelimiter(limit=10, window=1)
async def habit_tick(habit: Habit, day: datetime.date, value: bool | None, name_link: HabitLink | None = None):
    # Get current record
    records = await get_habit_checks(habit.id, habit.user_id)
    record = next((r for r in records if r.day == day), None)
    
    if record and record.done == value:  # Use == to handle None case correctly
        return

    # Toggle the habit check, preserving any existing note
    text = record.text if record and hasattr(record, 'text') else None
    record = await toggle_habit_check(habit.id, habit.user_id, day, text, value)
    
    # Get updated state from API
    from beaverhabits.frontend.components.index.habit.state import get_habit_state
    state = await get_habit_state(habit, day)
    
    # Update the name link color if provided
    if name_link:
        await name_link._update_style(state.color)

class BaseHabitCheckBox(ui.checkbox):
    def __init__(self, habit: Habit, day: datetime.date, value: bool | None, name_link: HabitLink | None = None, priority_label: HabitPriority | None = None) -> None:
        # Initialize with the actual state
        super().__init__("", value=value if value is not None else False)
        self.habit = habit
        self.day = day
        self.name_link = name_link
        self.priority_label = priority_label
        self.skipped = value is False  # Track skipped state (False means skipped, None means not set)
        ui.on('progress_complete_' + str(self.habit.id), self._handle_progress_complete)
        # Add data attributes for JavaScript
        self.props(f'data-habit-id="{habit.id}" data-day="{day}"')
        text_color = "chartreuse" if self.day == datetime.date.today() else settings.HABIT_COLOR_DAY_NUMBER
        self.unchecked_icon = icons.SQUARE.format(color="rgb(54,54,54)", text=self.day.day, text_color=text_color)
        self.checked_icon = icons.DONE
        self.skipped_icon = icons.CLOSE
        
        # Set up initial state
        self._update_icons()
        
        # Initialize state without async
        self.value = value if value is not None else False
        self.skipped = value is False  # False means skipped, None means not set
        
        # Update visual state
        if self.skipped:
            self.props("color=grey-8")
        else:
            self.props("color=currentColor" if self.value else "color=grey-8")
        
        # Hold on event flag
        self.hold = asyncio.Event()
        self.moving = False

    def _update_icons(self):
        if self.skipped:
            self.props(f'checked-icon="{self.skipped_icon}" unchecked-icon="{self.skipped_icon}" keep-color')
        elif self.value:
            self.props(f'checked-icon="{self.checked_icon}" unchecked-icon="{self.checked_icon}" keep-color')
        else:
            self.props(f'checked-icon="{self.unchecked_icon}" unchecked-icon="{self.unchecked_icon}" keep-color')

    def _update_state(self, value: bool | None):
        """Update the visual state of the checkbox."""
        # Update value first
        self.value = value if value is not None else False  # Update checkbox value
        
        # Then update internal state
        if value is None:  # Not set state
            self.skipped = False
        elif value is False:  # Skipped state
            self.skipped = True
        else:  # Checked state
            self.skipped = False
        
        # Then update visual state
        if self.skipped:
            self.props("color=grey-8")
        else:
            self.props("color=currentColor" if self.value else "color=grey-8")
        
        self._update_icons()
        self.update()          
        ui.run_javascript(f"window.showProgressbar('{self.habit.id}')")

    async def _handle_progress_complete(self, e):
        """Handle completion of progress bar animation."""     
        target_habit_id = int(e.args.get('habitId'))
        if target_habit_id == self.habit.id:
            logger.debug(f"Progress bar complete for habit {self.habit.id}")
            from beaverhabits.frontend.components.index.habit.list import calculate_habit_priority
            priority = await calculate_habit_priority(self.habit)
            
            # Update priority label
            if self.priority_label:
                await self.priority_label._update_priority(priority)
            
            # Update card data attribute and resort
            ui.run_javascript(f'''
                const card = document.querySelector('.habit-card[data-habit-id="{self.habit.id}"]');
                if (card) {{
                    card.setAttribute('data-priority', '{priority}');
                    window.sortHabits();
                }}
            ''')


    async def _mouse_down_event(self, e):
        self.hold.clear()
        self.moving = False

        try:
            async with asyncio.timeout(0.2):
                await self.hold.wait()
        except asyncio.TimeoutError:
            if settings.ENABLE_HABIT_NOTES:
                value = await note_tick(self.habit, self.day)
                # Note dialog handles its own state updates
                if value is not None:
                    self._update_state(value)
            else:
                # Skip note dialog, just toggle to checked state
                value = True                
                await habit_tick(self.habit, self.day, value, getattr(self, 'name_link', None))
        else:
            if self.moving:
                return
            # Get current state from database
            records = await get_habit_checks(self.habit.id, self.habit.user_id)
            record = next((r for r in records if r.day == self.day), None)
            current_state = record.done if record else None
            
            # Determine next state based on current database state
            if current_state is None:  # Currently not set
                value = True  # Move to checked
            elif current_state:  # Currently checked
                value = False  # Move to skipped
            else:  # Currently skipped
                value = None  # Move to not set
            
            try:
               await habit_tick(self.habit, self.day, value, getattr(self, 'name_link', None))    
            except Exception as e:
                pass
        
            self._update_state(value)    

    async def _mouse_up_event(self, e):
        self.hold.set()

    async def _mouse_move_event(self):
        self.moving = True
        self.hold.set()

class HabitCheckBox(BaseHabitCheckBox):
    def __init__(self, habit: Habit, day: datetime.date, value: bool | None, name_link: HabitLink | None = None, priority_label: HabitPriority | None = None) -> None:
        super().__init__(habit, day, value, name_link, priority_label)

        # Event handlers
        self.on("mousedown", self._mouse_down_event)
        self.on("touchstart", self._mouse_down_event)
        self.on("mouseup.prevent", self._mouse_up_event)
        self.on("touchend.prevent", self._mouse_up_event)
        self.on("touchmove", self._mouse_move_event)

class HabitStarCheckbox(ui.checkbox):
    def __init__(self, habit: Habit, refresh: Callable) -> None:
        super().__init__("", value=habit.star)
        self.habit = habit
        self.refresh = refresh
        self.props("dense fab-mini color=yellow-8")
        self.props('checked-icon="star" unchecked-icon="star_outline" size="sm"')
        self.on("change", self._async_task)

    async def _async_task(self, e):
        self.habit.star = e.value
        
        self.refresh()
        
        # Get updated state from API
        from beaverhabits.frontend.components.index.habit.state import get_habit_state
        state = await get_habit_state(self.habit, datetime.date.today())
        
        # Only use JavaScript for card sorting
        ui.run_javascript(f"window.updateHabitState('{self.habit.id}', {state.model_dump_json()})")

class CalendarCheckBox(BaseHabitCheckBox):
    def __init__(
        self,
        habit: Habit,
        day: datetime.date,
        today: datetime.date,
        initial_value: bool | None = False,
    ) -> None:
        # Pass the initial value to super()
        super().__init__(habit, day, initial_value)
        self.today = today
        
        self.classes("inline-block w-14")  # w-14 = width: 56px
        self.props("dense")
        
        # Event handlers
        self.on("mousedown", self._mouse_down_event)
        self.on("touchstart", self._mouse_down_event)
        self.on("mouseup.prevent", self._mouse_up_event)
        self.on("touchend.prevent", self._mouse_up_event)
        self.on("touchmove", self._mouse_move_event)
        self.on("click.prevent", lambda _: None)  # Prevent default click behavior
        self.on("change.prevent", lambda _: None)  # Prevent default change behavior

    @classmethod
    async def create(
        cls,
        habit: Habit,
        day: datetime.date,
        today: datetime.date,
    ) -> 'CalendarCheckBox':
        """Factory method to create a CalendarCheckBox with async initialization."""
        # Get initial state
        records = await get_habit_checks(habit.id, habit.user_id)
        record = next((r for r in records if r.day == day), None)
        initial_value = record.done if record else None  # None means not set
        
        # Create instance with initial value
        return cls(habit, day, today, initial_value)
