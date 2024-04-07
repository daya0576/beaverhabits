from enum import Enum
from pydantic_settings import BaseSettings

import logging

logging.getLogger("niceGUI").setLevel(logging.INFO)


class StorageType(Enum):
    SESSION = "session"
    SQLITE = "sqlite"


class Settings(BaseSettings):
    ENV: str = "dev"
    GUI_MOUNT_PATH: str = "/gui"
    # UI config
    INDEX_HABIT_ITEM_COUNT: int = 5
    # System
    NICEGUI_STORAGE_SECRET: str = "dev"
    # Storage
    STORAGE: StorageType = StorageType.SQLITE
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    def is_dev(self):
        return self.ENV == "dev"


settings = Settings()
