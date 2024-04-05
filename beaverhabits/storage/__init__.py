from beaverhabits.configs import StorageType
from beaverhabits.storage.storage import UserStorage
from .session import NiceGUISessionStorage, SessionStorage


session_storage = NiceGUISessionStorage()
sqlite_storage = None


def get_sessions_storage() -> SessionStorage:
    return session_storage


def get_user_storage(self) -> UserStorage:
    if self.STORAGE == StorageType.SQLITE:
        return None
