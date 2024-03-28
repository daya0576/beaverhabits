from beaverhabits.configs import StorageType
from .session import SessionStorage


session_storage = SessionStorage()
sqlite_storage = None


def storage(self):
    if self.STORAGE == StorageType.SQLITE:
        return None
    elif self.STORAGE == StorageType.SESSION:
        return session_storage
