from datetime import date
from typing import List, Optional
from pydantic import BaseModel

class CompletionRecord(BaseModel):
    """Single completion record for batch updates"""
    date: str
    done: bool

class HabitCompletions(BaseModel):
    """Batch update model for habit completions"""
    habit_id: int
    dates: List[str]

class Tick(BaseModel):
    """Single habit completion toggle"""
    date: str
    date_fmt: str = "%Y-%m-%d"
    done: bool = True

class HabitListMeta(BaseModel):
    """Metadata for habit lists"""
    order: Optional[List[int]] = None
