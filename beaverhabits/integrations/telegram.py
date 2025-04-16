from io import BytesIO

import requests

from beaverhabits.logging import logger


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
