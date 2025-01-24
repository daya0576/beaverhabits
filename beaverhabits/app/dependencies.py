from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security.utils import get_authorization_scheme_param
from starlette.status import HTTP_401_UNAUTHORIZED

from beaverhabits.app.auth import user_create, user_from_token, user_get_by_email
from beaverhabits.app.db import User
from beaverhabits.app.schemas import UserCreate
from beaverhabits.app.users import UserManager, get_user_manager
from beaverhabits.configs import settings


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
    if trusted_header_email and (user := await user_get_by_email(trusted_header_email)):
        return user

    if trusted_local_email:
        if user := await user_get_by_email(trusted_local_email):
            return user
        return await user_create(trusted_local_email)

    if credentials and (user := await user_from_token(credentials)):
        return user

    # ref: fastapi.security.oauth2.OAuth2PasswordBearer
    raise HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
