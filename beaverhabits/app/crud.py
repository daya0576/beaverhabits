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
        logger.debug(f"[CRUD] User {user.id} habit list query result: {habit_list is not None}")

        if not habit_list:
            logger.debug(f"[CRUD] Creating new habit list for user {user.id}")
            logger.debug(f"[CRUD] Initial data: {data}")
            session.add(
                HabitListModel(data=data, user_id=user.id),
            )
            await session.commit()
            logger.info(f"[CRUD] User {user.id} habit list created")
            return

        # Convert DatabasePersistentDict to dict for comparison
        data_dict = dict(data)
        logger.debug(f"[CRUD] Comparing data for user {user.id}:")
        logger.debug(f"[CRUD] Existing data: {habit_list.data}")
        logger.debug(f"[CRUD] New data: {data_dict}")
        if habit_list.data == data_dict:
            logger.warning(f"[CRUD] User {user.id} habit list unchanged")
            return

        logger.debug(f"[CRUD] Updating habit list for user {user.id}")
        habit_list.data = data_dict
        await session.commit()
        logger.info(f"[CRUD] User {user.id} habit list updated successfully")


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
