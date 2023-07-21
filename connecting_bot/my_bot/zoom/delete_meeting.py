import datetime
import json
import logging
from base64 import b64encode
from http import HTTPStatus


import requests

from connecting_bot.my_bot.bot_spec import scheduler
from connecting_bot.my_bot.db.db_commands import set_none, get_zoom_data, get_zoom_data_for_delete


# https://us05web.zoom.us/j/87025896454?pwd=nIXuF5OqAkp78jTxzJwKwpF9AMxNnI.1
# account_id = "d12h_-R_TWyIuD5u05e5iw"
# client_id = "GR4qNzNuSa6KZ1mHOYw0fA"
# client_secret = "5eOzBcgj0pdBfn0lxRAlC1zrFh4uPGfY"



def get_token(meeting_id):
    account_id, client_id, client_secret = get_zoom_data_for_delete(meeting_id)
    url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={account_id}"

    b64_client = f"{client_id}:{client_secret}".encode()
    b64_client = b64encode(b64_client).decode()
    headers = {"Authorization": f"Basic {b64_client}"}

    r = requests.post(url=url, headers=headers)
    if r.status_code == HTTPStatus.OK:
        return str(r.json()["access_token"])
    else:
        raise Exception("Ebuchie。")

# eyJzdiI6IjAwMDAwMSIsImFsZyI6IkhTNTEyIiwidiI6IjIuMCIsImtpZCI6ImE4ZGJkNDBmLWRlOTgtNGM0OS05MTQ4LTFlYmZhMDIxODkyNSJ9.eyJhdWQiOiJodHRwczovL29hdXRoLnpvb20udXMiLCJ1aWQiOiJVeGI5V3ZxVVFWZXg5V1pXaG02VGhBIiwidmVyIjo5LCJhdWlkIjoiMzM4ZmQyNjcwZmRlZjYxN2MzYTA5YjFmOTNhYTI2NzgiLCJuYmYiOjE2ODk0MDQ0MjMsImNvZGUiOiJXdDNWMHVaSFNiQ2NRSUtXQ21vdDRnSFc3UnhKVDcwbDMiLCJpc3MiOiJ6bTpjaWQ6R1I0cU56TnVTYTZLWjFtSE9ZdzBmQSIsImdubyI6MCwiZXhwIjoxNjg5NDA4MDIzLCJ0eXBlIjozLCJpYXQiOjE2ODk0MDQ0MjMsImFpZCI6ImQxMmhfLVJfVFd5SXVENXUwNWU1aXcifQ.GemclR5UbbcaSn4P7_i-yiccLwwku-Ku1nhGOPk_BR4WZvqQiO_7AsRviq78-Twj1m4EEvTNvRa3dKDeIizuEQ
# 82017040938
# https://us05web.zoom.us/s/82017040938?zak=eyJ0eXAiOiJKV1QiLCJzdiI6IjAwMDAwMSIsInptX3NrbSI6InptX28ybSIsImFsZyI6IkhTMjU2In0.eyJhdWQiOiJjbGllbnRzbSIsInVpZCI6IlV4YjlXdnFVUVZleDlXWldobTZUaEEiLCJpc3MiOiJ3ZWIiLCJzayI6IjAiLCJzdHkiOjEwMCwid2NkIjoidXMwNSIsImNsdCI6MCwibW51bSI6IjgyMDE3MDQwOTM4IiwiZXhwIjoxNjg5NDExNjI0LCJpYXQiOjE2ODk0MDQ0MjQsImFpZCI6ImQxMmhfLVJfVFd5SXVENXUwNWU1aXciLCJjaWQiOiIifQ.T89xef_7Va8bC_6zEpQTvIL_wg9PTY0N6v2I6BCXChY
# https://us05web.zoom.us/j/82017040938?pwd=zEIAJCSpHtqaUXaxGA93O7py3Nuba7.1
def delete_meeting_data(meeting_id):
    access_token = get_token(meeting_id)

    url = f"https://api.zoom.us/v2/meetings/{str(meeting_id)}"
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    r = requests.delete(url=url, headers=headers)
    print(r.status_code)
    if r.status_code == HTTPStatus.NO_CONTENT:
        logging.info('Старая встреча удалена')
        set_none(meeting_id)
    else:
        scheduler.add_job(func=delete_meeting_data, trigger='date',
                          run_date=datetime.datetime.now() + datetime.timedelta(minutes=1),
                          kwargs={'id': meeting_id})
        logging.info('Старая встреча не была удалена, попробуем позднее')



