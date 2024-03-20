import contextlib
from typing import Optional

from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.exceptions import UserAlreadyExists

from beaverhabits.app.schemas import UserCreate

from .users import get_jwt_strategy, get_user_manager
from .db import User, get_async_session, get_user_db


get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def user_authenticate(email: str, password: str) -> Optional[User]:
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    # user_logout()
                    credentials = OAuth2PasswordRequestForm(
                        username=email, password=password
                    )
                    user = await user_manager.authenticate(credentials)
                    if user is None or not user.is_active:
                        return None
                    return user
    except:
        return None


async def user_create_token(user: User) -> Optional[str]:
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db):
                    if user is None:
                        return None
                    strategy = get_jwt_strategy()
                    token = await strategy.write_token(user)
                    if token is not None:
                        return token
                    else:
                        return None
    except:
        return None


async def user_check_token(token: str) -> bool:
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    if token is None:
                        return False
                    strategy = get_jwt_strategy()
                    user = await strategy.read_token(token, user_manager)
                    if user is None or not user.is_active:
                        return False
                    else:
                        return True
    except:
        return False


async def user_create(
    email: str, password: str, is_superuser: bool = False
) -> Optional[User]:
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.create(
                        UserCreate(
                            email=email,
                            password=password,
                            is_superuser=is_superuser,
                        )
                    )
                    return user
    except UserAlreadyExists:
        raise
