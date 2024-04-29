import datetime
import hashlib

WEEK_DAYS = 7


def dummy_days(days: int) -> list[datetime.date]:
    today = datetime.date.today()
    return [today - datetime.timedelta(days=i) for i in reversed(range(days))]


def generate_hash_id(name: str) -> str:
    h = hashlib.new("sha1")
    h.update(name.encode())
    h.update(str(datetime.datetime.now()).encode())
    return h.hexdigest()[:6]
