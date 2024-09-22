import calendar
from enum import Enum
from pydantic_settings import BaseSettings

import logging

import dotenv

logging.getLogger("niceGUI").setLevel(logging.INFO)
dotenv.load_dotenv()

USER_DATA_FOLDER = ".user"


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

    # Storage
    HABITS_STORAGE: StorageType = StorageType.USER_DATABASE
    DATABASE_URL: str = f"sqlite+aiosqlite:///./{USER_DATA_FOLDER}/habits.db"
    MAX_USER_COUNT: int = -1

    # Customization
    FIRST_DAY_OF_WEEK: int = calendar.MONDAY

    def is_dev(self):
        return self.ENV == "dev"


settings = Settings()
