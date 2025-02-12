import asyncio
import datetime
from typing import Callable

from nicegui import ui, events

from beaverhabits.configs import settings
from beaverhabits.frontend import icons
from beaverhabits.logging import logger
from beaverhabits.storage.storage import CheckedRecord, Habit, get_week_ticks
from ..utils import ratelimiter

DAILY_NOTE_MAX_LENGTH = 300

def habit_tick_dialog(record: CheckedRecord | None):
    text = record.text if record else ""
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
    record = habit.record_by(day)
    result = await habit_tick_dialog(record)

    if result is None:
        return

    yes, text = result
    if text and len(text) > DAILY_NOTE_MAX_LENGTH:
        ui.notify("Note is too long", color="negative")
        return

    record = await habit.tick(day, yes, text)
    logger.info(f"Habit ticked: {day} {yes}, note: {text}")
    return record.done

@ratelimiter(limit=30, window=30)
@ratelimiter(limit=10, window=1)
async def habit_tick(habit: Habit, day: datetime.date, value: bool | None):
    # Avoid duplicate tick
    record = habit.record_by(day)
    logger.info(f"habit_tick: Initial record state: {record.done if record else None}")
    
    if record and record.done is value:  # Use 'is' to handle None case correctly
        logger.info(f"habit_tick: Skipping duplicate tick (value={value})")
        return

    # Transaction start
    logger.info(f"habit_tick: Setting new state to: {value}")
    await habit.tick(day, value)
    
    # Verify the state change
    new_record = habit.record_by(day)
    logger.info(f"habit_tick: New record state: {new_record.done if new_record else None}")

class BaseHabitCheckBox(ui.checkbox):
    def __init__(self, habit: Habit, day: datetime.date, value: bool | None) -> None:
        logger.info(f"Initializing checkbox for day {day} with value: {value}")
        # Initialize with the actual state
        super().__init__("", value=value if value is not None else False)
        self.habit = habit
        self.day = day
        self.skipped = value is None  # Track skipped state
        text_color = "chartreuse" if self.day == datetime.date.today() else "white"
        self.unchecked_icon = icons.SQUARE.format(color="rgb(54,54,54)", text=self.day.day, text_color=text_color)
        self.checked_icon = icons.DONE
        self.skipped_icon = icons.CLOSE
        
        # Set up initial state
        logger.info(f"Setting up initial state for day {day}: value={value}, skipped={self.skipped}")
        self._update_icons()
        self._update_style(value)

        # Hold on event flag
        self.hold = asyncio.Event()
        self.moving = False

    def _update_icons(self):
        logger.info(f"_update_icons: skipped={self.skipped}, value={self.value}")
        if self.skipped:
            logger.info("Setting skipped icons")
            self.props(f'checked-icon="{self.skipped_icon}" unchecked-icon="{self.skipped_icon}" keep-color')
        elif self.value:
            logger.info("Setting checked icons")
            self.props(f'checked-icon="{self.checked_icon}" unchecked-icon="{self.checked_icon}" keep-color')
        else:
            logger.info("Setting unchecked icons")
            self.props(f'checked-icon="{self.unchecked_icon}" unchecked-icon="{self.unchecked_icon}" keep-color')

    async def _update_style(self, value: bool | None):
        logger.info(f"_update_style called with value: {value}, current skipped: {self.skipped}")
        
        # First update internal state
        if value is None:  # Skipped state
            logger.info("Setting skipped state")
            self.value = True  # Show skipped icon
            self.skipped = True
        else:
            logger.info(f"Setting normal state: value={value}")
            self.value = value
            self.skipped = False
        
        # Then update visual state
        if self.skipped:
            self.props("color=grey-8")
        else:
            self.props("color=currentColor" if self.value else "color=grey-8")
        
        self._update_icons()
        logger.info(f"After _update_style: value={self.value}, skipped={self.skipped}")
            
        # Add a small delay to ensure habit state is updated
        await asyncio.sleep(0.1)
            
        # Get fresh ticked days after state update
        ticked_days = set(self.habit.ticked_days)
        if value:  # Add current day if it's being checked
            ticked_days.add(self.day)
        elif value is False:  # Remove current day if it's being unchecked
            ticked_days.discard(self.day)
            
        # Get ticks for current week using shared function
        week_ticks, _ = get_week_ticks(self.habit, self.day)
        
        # Check if this habit is skipped today
        is_skipped_today = (
            self.day == datetime.date.today() and 
            self.habit.record_by(self.day) and 
            self.habit.record_by(self.day).done is None
        )
        
        # Log Python-side state
        logger.info(f"Updating habit color: id={self.habit.id}, goal={self.habit.weekly_goal}, ticks={week_ticks}, skipped={is_skipped_today}")
        
        # Update state directly without refreshing
        ui.run_javascript(f"""
        if (!window.habitColorState) {{
            console.error('Habit color state not initialized - check script loading');
            return;
        }}

        debugLog('Updating habit from Python:', {{
            habitId: '{self.habit.id}',
            weeklyGoal: {self.habit.weekly_goal or 0},
            weekTicks: {week_ticks},
            isSkippedToday: {str(is_skipped_today).lower() if is_skipped_today is not None else 'null'}
        }});

        try {{
            // Update all elements with this habit ID
            const habitElements = document.querySelectorAll(`[data-habit-id="{self.habit.id}"]`);
            debugLog(`Found ${{habitElements.length}} elements for habit {self.habit.id}`);
            
            habitElements.forEach(element => {{
                debugLog('Updating element:', element);
                element.setAttribute('data-weekly-goal', '{self.habit.weekly_goal or 0}');
                element.setAttribute('data-week-ticks', '{week_ticks}');
                element.setAttribute('data-skipped', '{str(is_skipped_today).lower()}');
            }});
            
            // Call updateHabitColor to update the colors
            if (window.updateHabitColor) {{
                debugLog('Calling updateHabitColor');
                window.updateHabitColor(
                    '{self.habit.id}', 
                    {self.habit.weekly_goal or 0}, 
                    {week_ticks},
                    {str(is_skipped_today).lower() if is_skipped_today is not None else 'null'}
                );
            }} else {{
                console.error('updateHabitColor function not found - check script loading');
            }}
        }} catch (error) {{
            console.error('Error updating habit color:', error);
        }}
        """)

    async def _mouse_down_event(self, e):
        logger.info(f"Down event: {self.day}, {e.args.get('type')}")
        self.hold.clear()
        self.moving = False
        try:
            async with asyncio.timeout(0.2):
                await self.hold.wait()
        except asyncio.TimeoutError:
            if settings.ENABLE_HABIT_NOTES:
                value = await note_tick(self.habit, self.day)
                if value is not None:
                    await self._update_style(value)
            else:
                # Skip note dialog, just toggle to checked state
                value = True
                await habit_tick(self.habit, self.day, value)
                await self._update_style(value)
        else:
            if self.moving:
                logger.info("Mouse moving, skip...")
                return
            # Get current state from database
            record = self.habit.record_by(self.day)
            current_state = record.done if record else False
            logger.info(f"Current database state: {current_state}")
            
            # Determine next state based on current database state
            if current_state is None:  # Currently skipped
                logger.info("State: skipped -> original")
                value = False  # Move to original state
            elif current_state:  # Currently checked
                logger.info("State: checked -> skipped")
                value = None  # Move to skipped
            else:  # Currently unchecked
                logger.info("State: original -> checked")
                value = True  # Move to checked
            
            logger.info(f"Setting new state to: {value}")
            # Do update completion status
            await habit_tick(self.habit, self.day, value)
            # Update local state with latest data
            await self._update_style(value)
            logger.info(f"After state update: value={self.value}, skipped={self.skipped}")

    async def _mouse_up_event(self, e):
        logger.info(f"Up event: {self.day}, {e.args.get('type')}")
        self.hold.set()

    async def _mouse_move_event(self):
        self.moving = True
        self.hold.set()

class HabitCheckBox(BaseHabitCheckBox):
    def __init__(self, habit: Habit, day: datetime.date, value: bool | None, refresh: Callable | None = None) -> None:
        super().__init__(habit, day, value)
        self.refresh = refresh

        # Event handlers
        self.on("mousedown", self._mouse_down_event)
        self.on("touchstart", self._mouse_down_event)
        self.on("mouseup.prevent", self._mouse_up_event)
        self.on("touchend.prevent", self._mouse_up_event)
        self.on("touchmove", self._mouse_move_event)
        
        # Log initialization
        logger.info(f"HabitCheckBox initialized with refresh function: {refresh is not None}")

class HabitStarCheckbox(ui.checkbox):
    def __init__(self, habit: Habit, refresh: Callable) -> None:
        super().__init__("", value=habit.star)
        self.habit = habit
        self.refresh = refresh
        self.props("dense color=yellow-8")
        self.props('checked-icon="star" unchecked-icon="star_outline"')
        self.on("change", self._async_task)

    async def _async_task(self, e):
        self.habit.star = e.value
        logger.info(f"Star changed to {e.value}")
        self.refresh()

class CalendarCheckBox(BaseHabitCheckBox):
    def __init__(
        self,
        habit: Habit,
        day: datetime.date,
        today: datetime.date,
        is_bind_data: bool = True,
    ) -> None:
        # Get initial state before calling super()
        record = habit.record_by(day)
        initial_value = record.done if record else False
        logger.info(f"CalendarCheckBox init: day={day}, initial_value={initial_value}")
        
        # Pass the correct initial value to super()
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
