import json
from base64 import b64encode
from http import HTTPStatus

import requests
from loguru import logger

from connecting_bot.my_bot.db.db_commands import get_zoom_data, set_zoom_id


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
        raise Exception("create_meeting error status code")



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
        "timezone": "UTC",
        "join_before_host": False
    }
    r = requests.post(url=url, headers=headers, data=json.dumps(payload))
    if r.status_code == HTTPStatus.CREATED:
        set_zoom_id(account_id, int(r.json()["id"]))
        return str(r.json()["start_url"]), str(r.json()["join_url"]), int(r.json()["id"])
    else:
        logger.info('Не удалось создать встречу')
        raise Exception("error status code create meeting")
