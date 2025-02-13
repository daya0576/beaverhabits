from pydantic import BaseModel, EmailStr


class HabitListMeta(BaseModel):
    order: list[str] | None = None


class ExportCredentials(BaseModel):
    email: EmailStr
    password: str
    list_id: str | None = None
    archive: bool = False


class Tick(BaseModel):
    done: bool | None  # None means skipped
    date: str
    date_fmt: str = "%d-%m-%Y"


class HabitCompletion(BaseModel):
    date: str
    done: bool | None  # None means skipped


class HabitCompletions(BaseModel):
    email: EmailStr
    password: str
    habit_id: str
    completions: list[HabitCompletion]
    date_fmt: str = "%Y-%m-%d"
