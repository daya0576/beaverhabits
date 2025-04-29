import io
import json
from io import BytesIO

import requests

from beaverhabits.logger import logger
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import HabitList


def send_json_file(file: BytesIO, chat_id: str, token: str):
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    files = {"document": file}
    data = {"chat_id": chat_id}
    logger.debug(f"Sending file to Telegram: {url}, {data}")
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendDocument",
        files=files,
        data=data,
        timeout=5,
    )
    resp.raise_for_status()


def backup_to_telegram(token: str, chat_id: str, habit_list: HabitList):
    logger.info(f"Sending backup to Telegram chat {chat_id}")
    if not isinstance(habit_list, DictHabitList):
        raise TypeError("Habit list must be of type DictHabitList")

    binary_data = io.BytesIO(json.dumps(habit_list.data).encode())
    send_json_file(file=binary_data, token=token, chat_id=chat_id)
