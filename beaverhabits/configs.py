from enum import Enum
from pydantic_settings import BaseSettings


class StorageType(Enum):
    SESSION = "session"
    SQLITE = "sqlite"


class Settings(BaseSettings):
    # UI config
    INDEX_HABIT_ITEM_COUNT: int = 5
    # System
    NICEGUI_STORAGE_SECRET: str = "dev"
    # Storage
    STORAGE: StorageType = StorageType.SQLITE
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"


settings = Settings()
