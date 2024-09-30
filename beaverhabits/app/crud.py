import contextlib

from sqlalchemy import select

from beaverhabits.logging import logger

from .db import HabitListModel, User, get_async_session

get_async_session_context = contextlib.asynccontextmanager(get_async_session)


async def update_user_habit_list(user: User, data: dict) -> None:
    async with get_async_session_context() as session:
        stmt = select(HabitListModel).where(HabitListModel.user_id == user.id)
        result = await session.execute(stmt)
        habit_list = result.scalar()
        logger.info(f"[CRUD] User {user.id} habit list query")

        if not habit_list:
            session.add(
                HabitListModel(data=data, user_id=user.id),
            )
            await session.commit()
            logger.info(f"[CRUD] User {user.id} habit list created")
            return

        if habit_list.data == data:
            logger.warn(f"[CRUD] User {user.id} habit list unchanged")
            return

        habit_list.data = data
        await session.commit()
        logger.info(f"[CRUD] User {user.id} habit list updated")


async def get_user_habit_list(user: User) -> HabitListModel | None:
    async with get_async_session_context() as session:
        stmt = select(HabitListModel).where(HabitListModel.user_id == user.id)
        result = await session.execute(stmt)
        logger.info(f"[CRUD] User {user.id} habit list query")
        return result.scalar()


async def get_user_count() -> int:
    async with get_async_session_context() as session:
        stmt = select(User)
        result = await session.execute(stmt)
        user_count = len(result.all())
        logger.info(f"[CRUD] User count query: {user_count}")
        return user_count
