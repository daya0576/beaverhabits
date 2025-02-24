from nicegui import ui

class HabitGoalLabel(ui.label):
    def __init__(self, goal: int, initial_color: str | None = None) -> None:
        super().__init__(f"{int(goal)}x")
        self.classes("text-sm")
        
        # Set initial color if provided
        if initial_color:
            self.props(f"text-color={initial_color}")
    
    async def _update_style(self, color: str) -> None:
        """Update the visual state of the label."""
        self.props(f"text-color={color}")
