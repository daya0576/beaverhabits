from typing import List
from nicegui import ui

from beaverhabits.storage.storage import CheckedRecord

def habit_notes(records: List[CheckedRecord], limit: int = 10):
    with ui.timeline(side="right").classes("w-full pt-5 px-3 whitespace-pre-line"):
        for record in records[:limit]:
            color = "primary" if record.done else "grey-8"
            ui.timeline_entry(
                record.text,
                title="title",
                subtitle=record.day.strftime("%B %d, %Y"),
                color=color,
            )
