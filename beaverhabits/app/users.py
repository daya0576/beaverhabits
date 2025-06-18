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
async def change_user_password(user_id: uuid.UUID, old_password: str, new_password: str) -> bool:
    '''
    Changes the password for a given user.
    Returns True on success, raises HTTPException on failure.
    '''
    async for session in get_async_session(): # Iterate over the async generator
        async with session.begin(): # Start a transaction
            user_db = SQLAlchemyUserDatabase(session, User)
            user_manager = UserManager(user_db)

            user = await user_manager.get(user_id)
            if not user:
                logger.error(f"User with ID {user_id} not found for password change.")
                raise HTTPException(status_code=404, detail="User not found.")

            # Verify old password
            # UserManager.password_helper is usually available and public
            if not user_manager.password_helper.verify(old_password, user.hashed_password):
                logger.warning(f"Incorrect old password attempt for user {user_id}.")
                # Raising an exception that the frontend can catch and display
                raise InvalidPasswordException(reason="Incorrect old password.")

            # Update to new password
            try:
                await user_manager.update_password(user, new_password)
                logger.info(f"Password successfully changed for user {user_id}.")
                # fastapi-users' update_password already saves the user,
                # but if not, session.commit() would be needed here.
                # await session.commit() # Ensure changes are committed if user_manager doesn't do it.
                                        # UserManager.update() which is called by update_password handles the db update.
                return True
            except Exception as e:
                # Log the full exception for debugging
                logger.error(f"Error updating password for user {user_id}: {e}", exc_info=True)
                # Raise a generic error for the frontend
                raise HTTPException(status_code=500, detail=f"Failed to update password: {e}")
    # Fallback if session could not be established, though get_async_session should handle this
    return False
