import json
import uuid

from beaverhabits.app.db import User
from beaverhabits.storage.user_db import DatabasePersistentDict, UserDatabaseStorage
from beaverhabits.storage.user_file import FilePersistentDict, UserDiskStorage


async def test_disk_storage_deletion_removes_file_and_stops_backups(tmp_path):
    user = User(id=uuid.uuid4(), email="disk-delete@test.com")
    path = tmp_path / f"{user.email}.json"
    path.write_text(json.dumps({"data": {"habits": []}}), encoding="utf-8")

    persistent_dict = FilePersistentDict(path, encoding="utf-8")
    storage = UserDiskStorage()
    storage.user[user.id] = persistent_dict

    await storage.delete_user_habit_list(user)

    assert user.id not in storage.user
    assert not path.exists()

    persistent_dict["data"] = {"habits": [{"name": "must not return"}]}
    assert not path.exists()


async def test_database_storage_deletion_evicts_cache_and_stops_backups():
    user = User(id=uuid.uuid4(), email="database-delete@test.com")
    persistent_dict = DatabasePersistentDict(user, {"habits": []})
    storage = UserDatabaseStorage()
    storage.user[user.id] = persistent_dict

    await storage.delete_user_habit_list(user)

    assert user.id not in storage.user
    persistent_dict["habits"] = [{"name": "must not return"}]
