import datetime
from typing import AsyncGenerator, List

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from beaverhabits.configs import settings


DATABASE_URL = settings.DATABASE_URL


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    pass

    habits: Mapped[List["HabitModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class HabitModel(Base):
    __tablename__ = "habit"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))

    user: Mapped["User"] = relationship("User", back_populates="habits")
    records: Mapped[List["CheckedRecordModel"]] = relationship(back_populates="habit")

    def __repr__(self):
        return f"<HabitModel(name={self.name})>"


class CheckedRecordModel(Base):
    __tablename__ = "checked_record"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    day: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False)
    habit_id = Column(Integer, ForeignKey("habit.id"))

    habit = relationship("HabitModel", back_populates="records")

    def __repr__(self):
        return f"<CheckedRecordModel(day={self.day}, done={self.done})>"


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
