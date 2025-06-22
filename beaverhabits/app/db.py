import datetime
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import JSON, DateTime, ForeignKey, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

from beaverhabits.configs import settings

DATABASE_URL = settings.DATABASE_URL


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), insert_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), insert_default=func.now()
    )


class User(TimestampMixin, SQLAlchemyBaseUserTableUUID, Base):

    habit_list: Mapped["HabitListModel"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    configs: Mapped["UserConfigsModel"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    note_images: Mapped["UserNoteImageModel"] = relationship(
        back_populates="user", uselist=True, cascade="all, delete-orphan"
    )


class HabitListModel(TimestampMixin, Base):
    __tablename__ = "habit_list"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)

    user_id = mapped_column(GUID, ForeignKey("user.id"), index=True)
    user = relationship("User", back_populates="habit_list")


class UserIdentityModel(TimestampMixin, Base):
    __tablename__ = "customer"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(index=True, unique=True)
    customer_id: Mapped[str] = mapped_column(index=True, unique=True)
    provider: Mapped[str] = mapped_column(index=True)
    activated: Mapped[bool] = mapped_column(default=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)

    def __str__(self) -> str:
        return f"{self.email}<{self.customer_id}> ({self.provider})"


class UserConfigsModel(TimestampMixin, Base):
    __tablename__ = "user_configs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id = mapped_column(GUID, ForeignKey("user.id"), index=True)
    user = relationship("User", back_populates="configs")

    # Example config field
    config_data: Mapped[dict] = mapped_column(JSON, nullable=False)


class UserNoteImageModel(TimestampMixin, Base):
    __tablename__ = "user_note_images"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, index=True)
    user_id = mapped_column(GUID, ForeignKey("user.id"), index=True)
    user = relationship("User", back_populates="note_images")

    blob: Mapped[bytes] = mapped_column("blob", nullable=False)
    extra: Mapped[dict] = mapped_column(JSON, nullable=True)


# SSL Mode: https://www.postgresql.org/docs/9.0/libpq-ssl.html#LIBPQ-SSL-SSLMODE-STATEMENTS
# p.s. asyncpg us ssl instead of sslmode: https://github.com/tortoise/aerich/issues/310
connect_args = {}
if settings.DATABASE_URL.startswith("postgresql"):
    connect_args = {"ssl": "allow"}
engine = create_async_engine(
    DATABASE_URL, connect_args=connect_args, pool_pre_ping=True
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
