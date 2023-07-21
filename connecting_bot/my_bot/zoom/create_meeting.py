import json
import logging
from base64 import b64encode
from http import HTTPStatus

import requests

from connecting_bot.my_bot.db.db_commands import get_zoom_data, set_zoom_id

# https://us05web.zoom.us/j/87025896454?pwd=nIXuF5OqAkp78jTxzJwKwpF9AMxNnI.1
# account_id = "d12h_-R_TWyIuD5u05e5iw"
# client_id = "GR4qNzNuSa6KZ1mHOYw0fA"
# client_secret = "5eOzBcgj0pdBfn0lxRAlC1zrFh4uPGfY"





def get_token():
    account_id, client_id, client_secret = get_zoom_data()
    url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={account_id}"

    b64_client = f"{client_id}:{client_secret}".encode()
    b64_client = b64encode(b64_client).decode()
    headers = {"Authorization": f"Basic {b64_client}"}

    r = requests.post(url=url, headers=headers)
    if r.status_code == HTTPStatus.OK:
        return str(r.json()["access_token"]), account_id
    else:
        raise Exception("Ebuchie。")

# 85114389750
def create_meeting_data(topic, start_time):
    access_token, account_id = get_token()

    url = "https://api.zoom.us/v2/users/me/meetings"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "topic": topic,
        "start_time": start_time,
        "duration": 40,
        "timezone": "Asia/Almaty",
        "join_before_host": False
    }
    r = requests.post(url=url, headers=headers, data=json.dumps(payload))
    if r.status_code == HTTPStatus.CREATED:
        set_zoom_id(account_id, int(r.json()["id"]))
        return str(r.json()["start_url"]), str(r.json()["join_url"]), int(r.json()["id"])
    else:
        logging.info('Не удалось создать встречу')
        raise Exception("Kitayci")

