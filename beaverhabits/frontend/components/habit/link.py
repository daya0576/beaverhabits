from nicegui import ui

class HabitLink(ui.link):
    def __init__(self, text: str, target: str, initial_color: str | None = None) -> None:
        super().__init__(text, target=target)
        self.classes("dark:text-white no-underline hover:no-underline")
        
        # Set initial color if provided
        if initial_color:
            self.props(f"text-color={initial_color}")
    
    async def _update_style(self, color: str) -> None:
        """Update the visual state of the link."""
        self.props(f"text-color={color}")
