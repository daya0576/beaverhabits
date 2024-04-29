import calendar
from enum import Enum
from pydantic_settings import BaseSettings

import logging

logging.getLogger("niceGUI").setLevel(logging.INFO)


class StorageType(Enum):
    SESSION = "SESSION"
    USER_DATABASE = "DATABASE"
    USER_DISK = "USER_DISK"


class Settings(BaseSettings):
    ENV: str = "dev"

    # UI config
    INDEX_HABIT_ITEM_COUNT: int = 5

    # NiceGUI
    NICEGUI_STORAGE_SECRET: str = "dev"
    GUI_MOUNT_PATH: str = "/gui"
    DEMO_MOUNT_PATH: str = "/demo"

    # Quasar custom
    FIRST_DAY_OF_WEEK: int = calendar.MONDAY

    # Storage
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    HABITS_STORAGE: StorageType = StorageType.USER_DATABASE

    def is_dev(self):
        return self.ENV == "dev"


settings = Settings()
