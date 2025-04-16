import io
import json

from beaverhabits.integrations import telegram
from beaverhabits.logging import logger
from beaverhabits.storage.dict import DictHabitList
from beaverhabits.storage.storage import HabitList


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
    telegram.send_json_file(file=binary_data, token=token, chat_id=chat_id)
