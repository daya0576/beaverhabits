from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # UI config
    INDEX_HABIT_ITEM_COUNT: int = 5
    # System
    STORAGE_SECRET: str = "dev"
    # Storage
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"


settings = Settings()
