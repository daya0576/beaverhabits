import contextlib
from typing import Sequence

from sqlalchemy import select

from beaverhabits.logging import logger

from .db import HabitListModel, User, UserIdentityModel, get_async_session

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
            logger.warning(f"[CRUD] User {user.id} habit list unchanged")
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


async def get_user_list() -> Sequence[User]:
    async with get_async_session_context() as session:
        stmt = select(User).order_by(User.updated_at.desc())
        result = await session.execute(stmt)
        user_list = result.scalars().all()
        logger.info(f"[CRUD] User list query: {len(user_list)}")
        return user_list


async def get_customer_list() -> Sequence[UserIdentityModel]:
    async with get_async_session_context() as session:
        # Sorted by updated desc
        stmt = select(UserIdentityModel).order_by(UserIdentityModel.updated_at.desc())
        result = await session.execute(stmt)
        customer_list = result.scalars().all()
        logger.info(f"[CRUD] Customer list query: {customer_list}")
        return customer_list


async def get_user_identity(email: str) -> UserIdentityModel | None:
    async with get_async_session_context() as session:
        stmt = select(UserIdentityModel).where(UserIdentityModel.email == email)
        result = await session.execute(stmt)
        user_identity = result.scalar()
        logger.info(f"[CRUD] User identity query: {user_identity}")
        return user_identity


async def get_user_identity_by_id(
    customer_id: str,
) -> UserIdentityModel | None:
    async with get_async_session_context() as session:
        stmt = select(UserIdentityModel).where(
            UserIdentityModel.customer_id == customer_id
        )
        result = await session.execute(stmt)
        user_identity = result.scalar()
        logger.info(f"[CRUD] User identity query: {user_identity}")
        return user_identity


async def get_or_create_user_identity(
    email: str, customer_id: str, provider: str, data: dict
) -> UserIdentityModel:
    async with get_async_session_context() as session:
        stmt = select(UserIdentityModel).where(
            UserIdentityModel.email == email,
            UserIdentityModel.customer_id == customer_id,
        )
        result = await session.execute(stmt)
        user_identity = result.scalar()

        if not user_identity:
            user_identity = UserIdentityModel(
                email=email,
                customer_id=customer_id,
                provider=provider,
                data=data,
            )
            session.add(user_identity)
            await session.commit()
            logger.info(f"[CRUD] User identity created: {user_identity}")
        else:
            logger.info(f"[CRUD] User identity query: {user_identity}")

        return user_identity


async def update_user_identity(customer_id: str, data: dict, activate: bool) -> None:
    async with get_async_session_context() as session:
        stmt = select(UserIdentityModel).where(
            UserIdentityModel.customer_id == customer_id
        )
        result = await session.execute(stmt)
        user_identity = result.scalar()
        if not user_identity:
            raise ValueError(f"User identity with customer_id {customer_id} not found")

        user_identity.data = data
        user_identity.activated = activate
        await session.commit()
        logger.info(f"[CRUD] User identity updated: {user_identity}")
