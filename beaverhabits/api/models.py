from datetime import date
from typing import List, Optional, Any, Literal
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

class HabitSorting(BaseModel):
    """Sorting information for a habit"""
    starred: bool
    priority: int
    order: int
    name: str

class HabitUpdateResponse(BaseModel):
    """Response model for habit updates"""
    habit_id: int
    color: str
    state: Literal["checked", "skipped", "unset"]
    sorting: HabitSorting
