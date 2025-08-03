import contextlib
from typing import Optional
from uuid import UUID

import jwt
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import exceptions, models
from fastapi_users.exceptions import UserAlreadyExists
from fastapi_users.jwt import decode_jwt, generate_jwt
from fastapi_users.manager import RESET_PASSWORD_TOKEN_AUDIENCE
from nicegui import app

from beaverhabits.app.db import User, get_async_session, get_user_db
from beaverhabits.app.schemas import UserCreate
from beaverhabits.app.users import get_jwt_strategy, get_user_manager
from beaverhabits.configs import settings
from beaverhabits.logger import logger

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
        logger.exception("Unkownn Exception")
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
        raise Exception("User already exists!")


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


async def user_get_by_id(user_id: UUID) -> User:
    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                return await user_manager.get(user_id)


def user_logout() -> bool:
    app.storage.user.clear()
    return True


def user_create_reset_token(user: User) -> str:
    # Ref: https://github.com/fastapi-users/fastapi-users/blob/9d78b2a35dc7f35c2ffca67232c11f4d27a5db00/fastapi_users/manager.py#L358
    if not user.is_active:
        raise exceptions.UserInactive()

    token_data = {
        "sub": str(user.id),
        "aud": RESET_PASSWORD_TOKEN_AUDIENCE,
    }
    assert settings.RESET_PASSWORD_TOKEN_SECRET, "Missing JWT secret"
    token = generate_jwt(
        token_data,
        settings.RESET_PASSWORD_TOKEN_SECRET,
        settings.RESET_PASSWORD_TOKEN_LIFETIME_SECONDS,
    )

    return token


async def user_from_reset_token(token: str) -> User:
    # ref: https://github.com/fastapi-users/fastapi-users/blob/9d78b2a35dc7f35c2ffca67232c11f4d27a5db00/fastapi_users/manager.py#L386
    try:
        data = decode_jwt(
            token,
            settings.RESET_PASSWORD_TOKEN_SECRET,
            [RESET_PASSWORD_TOKEN_AUDIENCE],
        )
    except jwt.PyJWTError:
        raise exceptions.InvalidResetPasswordToken()

    try:
        user_id = data["sub"]
    except KeyError:
        raise exceptions.InvalidResetPasswordToken()

    user = await user_get_by_id(UUID(user_id))
    if not user.is_active:
        raise exceptions.UserInactive()

    return user


async def user_reset_password(user: User, new_password: str) -> User:
    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                updated_user = await user_manager._update(
                    user, {"password": new_password}
                )
                return updated_user


async def user_deletion(user: User) -> None:
    async with get_async_session_context() as session:
        async with get_user_db_context(session) as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                await user_manager.delete(user)
