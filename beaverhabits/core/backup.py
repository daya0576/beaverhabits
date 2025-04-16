import io
import json
from io import BytesIO

import requests

from beaverhabits.logging import logger
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import HabitList


def send_json_file(file: BytesIO, chat_id: str, token: str):
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    resp = requests.get(url, timeout=5)
    logger.debug(resp.json())

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


def backup_to_telegram(habit_list: HabitList):
    logger.info("Backing up habit list to Telegram")

    token = habit_list.backup.telegram_bot_token
    if not token:
        raise ValueError("Telegram bot token not found")
    chat_id = habit_list.backup.telegram_chat_id
    if not chat_id:
        raise ValueError("Telegram chat_id not found")

    if not isinstance(habit_list, DictHabitList):
        raise TypeError("Habit list must be of type DictHabitList")

    binary_data = io.BytesIO(json.dumps(habit_list.data).encode())
    send_json_file(file=binary_data, token=token, chat_id=chat_id)
