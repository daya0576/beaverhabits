from typing import AsyncGenerator
from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from beaverhabits.sql.database import get_async_session, create_db_and_tables
from beaverhabits.sql.models import User

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

# Re-export create_db_and_tables for use in main.py
__all__ = ['get_user_db', 'get_async_session', 'create_db_and_tables']
