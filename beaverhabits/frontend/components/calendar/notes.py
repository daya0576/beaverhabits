from typing import List
from nicegui import ui

from beaverhabits.sql.models import CheckedRecord

def habit_notes(records: List[CheckedRecord], limit: int = 10):
    # Sort records by date, most recent first
    sorted_records = sorted(records, key=lambda r: r.day, reverse=True)
    
    with ui.timeline(side="right").classes("w-full pt-5 px-3 whitespace-pre-line"):
        for record in sorted_records[:limit]:
            color = "primary" if record.done else "grey-8"
            ui.timeline_entry(
                record.text if hasattr(record, 'text') else '',  # Handle records without text
                title="title",
                subtitle=record.day.strftime("%B %d, %Y"),
                color=color,
            )
