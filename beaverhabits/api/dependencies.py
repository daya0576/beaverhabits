from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from beaverhabits.app.db import User
from beaverhabits.app.dependencies import current_active_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/jwt/login")

async def get_current_user(
    user: User = Depends(current_active_user),
) -> User:
    """Get the current authenticated user."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
