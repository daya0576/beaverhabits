import contextlib
from typing import List
from sqlalchemy import select

from .db import HabitModel, User, get_async_session

get_async_session_context = contextlib.asynccontextmanager(get_async_session)


async def create_user_habit(user: User, name: str) -> HabitModel:
    async with get_async_session_context() as session:
        db_habit = HabitModel(name=name, user=user)
        session.add(db_habit)
        await session.commit()
        await session.refresh(db_habit)
        return db_habit


async def get_user_habit_list(user: User) -> List[HabitModel]:
    async with get_async_session_context() as session:
        stmt = select(HabitModel).where(HabitModel.user == user)
        result = await session.execute(stmt)
        return [x for x in result.scalars()]
