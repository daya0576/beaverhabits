from beaverhabits.configs import StorageType, settings
from beaverhabits.storage.session_memory import SessionDictStorage
from beaverhabits.storage.storage import SessionStorage, UserStorage
from beaverhabits.storage.user_db import UserDatabaseStorage
from beaverhabits.storage.user_file import UserDiskStorage

session_storage = SessionDictStorage()
user_disk_storage = UserDiskStorage()
user_database_storage = UserDatabaseStorage()
sqlite_storage = None


def get_sessions_storage() -> SessionStorage:
    return session_storage


def get_user_dict_storage() -> UserStorage:
    if settings.HABITS_STORAGE == StorageType.USER_DISK:
        return user_disk_storage

    if settings.HABITS_STORAGE == StorageType.USER_DATABASE:
        return user_database_storage

    raise NotImplementedError("Storage type not implemented")
