import contextlib
from typing import Optional

from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.exceptions import UserAlreadyExists
from nicegui import app

from beaverhabits.app.db import User, get_async_session, get_user_db
from beaverhabits.app.schemas import UserCreate
from beaverhabits.app.users import get_jwt_strategy, get_user_manager
from beaverhabits.logging import logger

get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def user_authenticate(email: str, password: str) -> Optional[User]:
    try:
        logger.info(f"Starting authentication for email: {email}")
        async with get_async_session_context() as session:
            logger.debug("Database session created")
            async with get_user_db_context(session) as user_db:
                logger.debug("User database context acquired")
                async with get_user_manager_context(user_db) as user_manager:
                    logger.debug("User manager context acquired")
                    credentials = OAuth2PasswordRequestForm(
                        username=email, password=password
                    )
                    try:
                        user = await user_manager.authenticate(credentials)
                        if user is None:
                            logger.error(f"Authentication failed for email: {email} - User not found")
                            return None
                        if not user.is_active:
                            logger.error(f"Authentication failed for email: {email} - User not active")
                            return None
                        logger.info(f"Authentication successful for email: {email}")
                        return user
                    except Exception as e:
                        logger.error(f"Authentication error for email: {email}: {str(e)}")
                        return None
    except Exception as e:
        logger.exception(f"Database connection error during authentication for email: {email}")
        return None


async def user_create_token(user: User) -> Optional[str]:
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db):
                    strategy = get_jwt_strategy()
                    token = await strategy.write_token(user)
                    if token is not None:
                        return token
                    else:
                        return None
    except:
        return None


async def user_check_token(token: str | None) -> bool:
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    if token is None:
                        return False
                    strategy = get_jwt_strategy()
                    user = await strategy.read_token(token, user_manager)
                    return bool(user and user.is_active)
    except:
        return False


async def user_from_token(token: str | None) -> User | None:
    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                if not token:
                    return None
                strategy = get_jwt_strategy()
                user = await strategy.read_token(token, user_manager)
                return user


async def user_create(
    email: str, password: str = "", is_superuser: bool = False
) -> User:
    try:
        logger.info(f"Starting user creation for email: {email}")
        async with get_async_session_context() as session:
            logger.debug("Database session created for user creation")
            async with get_user_db_context(session) as user_db:
                logger.debug("User database context acquired for user creation")
                async with get_user_manager_context(user_db) as user_manager:
                    logger.debug("User manager context acquired for user creation")
                    try:
                        user = await user_manager.create(
                            UserCreate(
                                email=email,
                                password=password,
                                is_superuser=is_superuser,
                            )
                        )
                        logger.info(f"Successfully created user with email: {email}")
                        return user
                    except Exception as e:
                        logger.error(f"Error creating user with email {email}: {str(e)}")
                        raise
    except UserAlreadyExists:
        logger.error(f"User creation failed - User already exists with email: {email}")
        raise Exception("User already exists!")
    except Exception as e:
        logger.exception(f"Database error during user creation for email: {email}")
        raise Exception(f"Failed to create user: {str(e)}")


async def user_get_by_email(email: str) -> Optional[User]:
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.get_by_email(email)
                    return user
    except:
        logger.exception("Unkownn Exception")
        return None


def user_logout() -> bool:
    app.storage.user.update({"auth_token": ""})
    return True
