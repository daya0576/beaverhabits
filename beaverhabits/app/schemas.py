import datetime
import uuid
from typing import List, Optional

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class CheckedRecordBase(BaseModel):
    day: datetime.date
    done: bool


class CheckedRecordCreate(CheckedRecordBase):
    pass


class CheckedRecordRead(CheckedRecordBase):
    id: str
    habit_id: int

    class Config:
        from_attributes = True


class HabitBase(BaseModel):
    name: str
    order: int = 0


class HabitCreate(HabitBase):
    list_id: int


class HabitUpdate(BaseModel):
    name: Optional[str] = None
    order: Optional[int] = None
    list_id: Optional[int] = None


class HabitRead(HabitBase):
    id: int
    list_id: int
    user_id: uuid.UUID
    checked_records: List[CheckedRecordRead] = []

    class Config:
        from_attributes = True


class HabitListBase(BaseModel):
    name: str
    order: int = 0


class HabitListCreate(HabitListBase):
    pass


class HabitListUpdate(BaseModel):
    name: Optional[str] = None
    order: Optional[int] = None


class HabitListRead(HabitListBase):
    id: int
    user_id: uuid.UUID
    habits: List[HabitRead] = []

    class Config:
        from_attributes = True
