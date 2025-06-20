import uuid
from typing import Optional

from fastapi import Depends, Request, HTTPException
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi_users.exceptions import InvalidPasswordException
from passlib.context import CryptContext

from beaverhabits.configs import settings
from beaverhabits.logging import logger

from .db import User, get_user_db, get_async_session

JWT_SECRET = settings.JWT_SECRET
JWT_LIFETIME_SECONDS = settings.JWT_LIFETIME_SECONDS


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = JWT_SECRET
    verification_token_secret = JWT_SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        logger.info(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.info(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.info(
            f"Verification requested for user {user.id}. Verification token: {token}"
        )


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
jwt_strategy = JWTStrategy(secret=JWT_SECRET, lifetime_seconds=JWT_LIFETIME_SECONDS)


def get_jwt_strategy() -> JWTStrategy:
    return jwt_strategy


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# New function to be added:
async def change_user_password(user_manager: UserManager, user_id: uuid.UUID, old_password: str, new_password: str) -> bool:
    '''
    Changes the password for a given user.
    Requires a UserManager instance obtained via FastAPI's dependency injection.
    Returns True on success, raises HTTPException on failure.
    '''
    # user_manager is now passed in, assumed to be correctly initialized.
    # Session and transaction management are handled by this injected user_manager.

    user = await user_manager.get(user_id)
    if not user: # Corrected indentation
        logger.error(f"User with ID {user_id} not found for password change.")
        raise HTTPException(status_code=404, detail="User not found.")

    # Conditionally verify old password using passlib CryptContext
    if not settings.SKIP_OLD_PASSWORD_CHECK_ON_CHANGE:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if not pwd_context.verify(old_password, user.hashed_password):
            logger.warning(f"Incorrect old password attempt for user {user_id}.")
            raise InvalidPasswordException(reason="Incorrect old password.")
    else:
        logger.warning(
            f"Skipping old password check for user {user_id} due to SKIP_OLD_PASSWORD_CHECK_ON_CHANGE setting."
        )

    # Update to new password
    try:
        # Hash and set the new password
        user.hashed_password = user_manager.password_helper.hash(new_password)
        await user_manager.user_db.update(user, {"hashed_password": user.hashed_password})
        logger.info(f"Password successfully changed for user {user_id}.")
        return True
    except Exception as e:
        logger.error(f"Error updating password for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update password: {e}")
    # This return False should ideally not be reached if all paths lead to True or an exception.
    return False
