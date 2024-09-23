import datetime
import uuid
from typing import List

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class HabitCreate(BaseModel):
    name: str


class HabitRead(BaseModel):
    id: int
    name: str

    user: UserRead
    items: List["CheckedRecord"]


class CheckedRecord(BaseModel):
    id: str
    day: datetime.date
    done: bool
    habit: "HabitRead"
