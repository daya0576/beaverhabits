from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security.utils import get_authorization_scheme_param
from fastapi_users.jwt import decode_jwt
from starlette.status import HTTP_401_UNAUTHORIZED

from beaverhabits import views
from beaverhabits.app.auth import (
    user_from_reset_token,
    user_from_token,
    user_get_by_email,
)
from beaverhabits.app.db import User
from beaverhabits.configs import settings
from beaverhabits.logger import logger


def get_bearer_token(request: Request) -> Optional[str]:
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None

    scheme, param = get_authorization_scheme_param(authorization)
    if scheme.lower() != "bearer":
        return None

    return param


def get_trusted_header_email(request: Request) -> Optional[str]:
    if not settings.TRUSTED_EMAIL_HEADER:
        return None

    return request.headers.get(settings.TRUSTED_EMAIL_HEADER)


def get_trusted_local_email() -> Optional[str]:
    return settings.TRUSTED_LOCAL_EMAIL


async def current_active_user(
    credentials: Annotated[Optional[str], Depends(get_bearer_token)],
    trusted_header_email: Annotated[Optional[str], Depends(get_trusted_header_email)],
    trusted_local_email: Annotated[Optional[str], Depends(get_trusted_local_email)],
) -> User:
    if trusted_header_email:
        if user := await user_get_by_email(trusted_header_email):
            return user
        else:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=f"Trusted email user not found: {trusted_header_email}",
            )

    if trusted_local_email:
        logger.info(f"Trusted local email: {trusted_local_email}")
        if user := await user_get_by_email(trusted_local_email):
            return user
        logger.info(f"Trusted local email user not found. Creating user.")
        user = await views.register_user(trusted_local_email)
        return user

    if credentials and (user := await user_from_token(credentials)):
        return user

    # ref: fastapi.security.oauth2.OAuth2PasswordBearer
    raise HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def current_admin_user(
    user: Annotated[User, Depends(current_active_user)],
) -> User:
    if user.email != settings.ADMIN_EMAIL:
        logger.warning(
            f"User {user.email} tried to access admin endpoint without admin privileges."
        )
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_reset_user(request: Request) -> User:
    token = request.query_params.get("token")
    if not token:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Token not found",
        )

    return await user_from_reset_token(token)
