import datetime
from typing import List
from uuid import UUID, uuid4
from sqlalchemy import ForeignKey, func, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from .database import Base

class TimestampMixin:
    """Mixin for adding created_at and updated_at timestamps"""
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), insert_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), insert_default=func.now(), onupdate=func.now()
    )

class User(TimestampMixin, SQLAlchemyBaseUserTableUUID, Base):
    """User model with relationships to habits and lists"""
    __tablename__ = "users"

    habits: Mapped[List["Habit"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    lists: Mapped[List["HabitList"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

class HabitList(TimestampMixin, Base):
    """List model for organizing habits"""
    __tablename__ = "lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(default=0)
    deleted: Mapped[bool] = mapped_column(default=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    user: Mapped["User"] = relationship(back_populates="lists")
    habits: Mapped[List["Habit"]] = relationship(
        back_populates="habit_list", cascade="all, delete-orphan"
    )

class Habit(TimestampMixin, Base):
    """Habit model with checked records"""
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(default=0)
    weekly_goal: Mapped[int | None] = mapped_column(default=0)
    deleted: Mapped[bool] = mapped_column(default=False)
    star: Mapped[bool] = mapped_column(default=False)
    list_id: Mapped[int | None] = mapped_column(ForeignKey("lists.id"), index=True, nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    user: Mapped["User"] = relationship(back_populates="habits")
    habit_list: Mapped["HabitList"] = relationship(back_populates="habits")
    checked_records: Mapped[List["CheckedRecord"]] = relationship(
        back_populates="habit", cascade="all, delete-orphan"
    )

class CheckedRecord(TimestampMixin, Base):
    """Record of habit completion status for a specific day"""
    __tablename__ = "checked_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    day: Mapped[datetime.date] = mapped_column(nullable=False)
    done: Mapped[bool] = mapped_column(default=False)
    text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id"), index=True)

    habit: Mapped["Habit"] = relationship(back_populates="checked_records")
