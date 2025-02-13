from pydantic import BaseModel, EmailStr


class HabitListMeta(BaseModel):
    order: list[str] | None = None


class ExportCredentials(BaseModel):
    email: EmailStr
    password: str
    list_id: str | None = None
    archive: bool = False


class Tick(BaseModel):
    done: bool
    date: str
    date_fmt: str = "%d-%m-%Y"
