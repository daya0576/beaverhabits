from beaverhabits.configs import StorageType
from beaverhabits.storage.storage import UserStorage
from beaverhabits.storage.user_file import UserDiskStorage
from beaverhabits.storage.session_file import SessionDictStorage, SessionStorage
from beaverhabits.configs import settings


session_storage = SessionDictStorage()
user_disk_storage = UserDiskStorage()
sqlite_storage = None


def get_sessions_storage() -> SessionStorage:
    return session_storage


def get_user_storage() -> UserStorage:
    if settings.HABITS_STORAGE == StorageType.USER_DISK:
        return user_disk_storage

    raise NotImplementedError("Storage type not implemented")
    # if self.STORAGE == StorageType.SQLITE:
    #     return None
