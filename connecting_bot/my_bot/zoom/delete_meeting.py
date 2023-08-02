import datetime
from base64 import b64encode
from http import HTTPStatus

import pytz
import requests
from loguru import logger

from connecting_bot.my_bot.bot_spec import scheduler
from connecting_bot.my_bot.db.db_commands import set_none, get_zoom_data_for_delete


def get_token(meeting_id):
    try:
        account_id, client_id, client_secret = get_zoom_data_for_delete(meeting_id)
        url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={account_id}"

        b64_client = f"{client_id}:{client_secret}".encode()
        b64_client = b64encode(b64_client).decode()
        headers = {"Authorization": f"Basic {b64_client}"}

        r = requests.post(url=url, headers=headers)
        if r.status_code == HTTPStatus.OK:
            return str(r.json()["access_token"])
        else:
            raise Exception("error status code delete meeting token")
    except Exception as err:
        logger.info(f'{err}')


def delete_meeting_data(meeting_id):
    try:
        access_token = get_token(meeting_id)
        url = f"https://api.zoom.us/v2/meetings/{str(meeting_id)}"
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        r = requests.delete(url=url, headers=headers)
        if r.status_code == HTTPStatus.NO_CONTENT:
            logger.info('Старая встреча удалена')
            set_none(meeting_id)
        else:
            run = datetime.datetime.now(pytz.timezone('UTC')) + datetime.timedelta(minutes=2)
            scheduler.add_job(func=delete_meeting_data, trigger='date',
                              run_date=run,
                              kwargs={'meeting_id': meeting_id},
                              timezone='UTC')
            logger.info('Старая встреча не была удалена, попробуем позднее')
    except Exception as err:
        logger.info(f'{err}')