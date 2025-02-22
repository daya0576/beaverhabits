from typing import AsyncGenerator
import configparser
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Read database settings from settings.ini
config = configparser.ConfigParser()
config.read('settings.ini')

db_config = config['database']
db_host = db_config.get('host', 'localhost')
db_port = db_config.get('port', '3306')
db_name = db_config.get('database', 'beaverhabits')
db_user = db_config.get('user', 'root')
db_password = db_config.get('password', '')

# Construct database URL
db_password_part = f":{db_password}@" if db_password else "@"
DATABASE_URL = f"mysql+aiomysql://{db_user}{db_password_part}{db_host}:{db_port}/{db_name}"

class Base(DeclarativeBase):
    pass

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False  # Set to True for SQL query logging
)

# Create async session maker
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def create_db_and_tables():
    """Create all tables that don't yet exist"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    async with async_session_maker() as session:
        yield session
