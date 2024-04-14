import datetime
import hashlib
from typing import List


def dummy_days(days: int) -> List[datetime.date]:
    today = datetime.date.today()
    return [today - datetime.timedelta(days=i) for i in reversed(range(days))]


def generate_hash_id(name: str) -> str:
    h = hashlib.new("sha1")
    h.update(name.encode())
    h.update(str(datetime.datetime.now()).encode())
    return h.hexdigest()[:6]
