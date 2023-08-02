import datetime
from asyncio import sleep

import pytz
from aiogram import types
from loguru import logger

from connecting_bot.my_bot.bot_spec import bot, scheduler
from connecting_bot.my_bot.db.db_commands import get_text, get_users, get_text_for_participants, \
    get_participants, delete_initiator_event, check_timezone
from connecting_bot.my_bot.keyboards.user_kb import ikm
from connecting_bot.my_bot.zoom.create_meeting import create_meeting_data
from connecting_bot.my_bot.zoom.delete_meeting import delete_meeting_data


# функции без хендлеров
# рассылка
async def msg_send_all(callback: types.CallbackQuery, event_id):
    users = get_users(event_id)
    if users != None:
        for user_id in users:
            try:
                text = get_text(event_id, user_id)
                bot = callback.bot
                await bot.send_message(chat_id=user_id,
                                       text=text,
                                       reply_markup=ikm(event_id))
                await sleep(0.3)
            except Exception:
                pass
    else:
        logger.info(f'По ивенту {event_id} нет подходящих под рассылку юзеров')


# отправка напоминания
async def send_reminder(event_id, ini_id, title, date):
    participant_list = get_participants(event_id)
    if participant_list:
        for user_id in participant_list:
            text = get_text_for_participants(event_id, user_id)
            if text:
                try:
                    await bot.send_message(chat_id=user_id,
                                           text=text)
                    await sleep(0.3)
                    logger.info('Пошла рассылочка')
                except Exception:
                    pass
    else:
        logger.info('Не найдено событие или нет участников. Напоминание не отправлено')
    dt = datetime.datetime.strptime(date, '%d-%m-%Y %H:%M')
    utc_tz = pytz.timezone('UTC')
    utc_datetime = utc_tz.localize(dt)  # дата ивента с часовым поясом ютс
    time_z = check_timezone(ini_id)
    tz = pytz.timezone(time_z)
    dat = dt.astimezone(tz)
    format_date = dat.strftime("%d-%m в %H:%M")
    await bot.send_message(chat_id=ini_id,
                           text=f'Напоминаю, что {format_date} состоится событие {title}, '
                                f'За 5 минут до начала Вам придёт ссылка-приглашение.')
    date_check = utc_datetime - datetime.timedelta(minutes=6)
    scheduler.add_job(func=check_availability_participants, trigger='date', run_date=date_check,
                      kwargs={'event_id': int(event_id), 'ini_id': ini_id, 'title': title},
                      misfire_grace_time=10, timezone='UTC')
    date_send = utc_datetime - datetime.timedelta(minutes=5)
    scheduler.add_job(func=send_url_to_users, trigger='date', run_date=date_send,
                      kwargs={'event_id': int(event_id), 'ini_id': ini_id, 'title': title},
                      misfire_grace_time=10, timezone='UTC')


# проверка, есть ли участники по ивенту
async def check_availability_participants(event_id, ini_id, title):
    try:
        list_of_participants = get_participants(event_id)
        if list_of_participants:
            pass
        else:
            await bot.send_message(chat_id=ini_id,
                                   text=f'По вашему ивенту {title} нет участников X(\n'
                                        f'Ивент не состоится. Попробуйте создать новый ивент '
                                        f'на другую дату.')
            delete_initiator_event(ini_id, event_id)
    except Exception as err:
        logger.info(f'{err}')


# отправляем ссылку инициатору и участникам
async def send_url_to_users(event_id, title, ini_id):
    try:
        participant_list = get_participants(event_id)
        if participant_list:
            run_delete = datetime.datetime.now(pytz.timezone('UTC')) + datetime.timedelta(minutes=50)
            dt_str = str(run_delete.strftime('%Y-%m-%d %H:%M:%S'))
            start_url, join_url, meeting_id = create_meeting_data(title, dt_str)
            scheduler.add_job(func=delete_meeting_data, trigger='date',
                              run_date=run_delete,
                              kwargs={'meeting_id': meeting_id},
                              timezone='UTC')
            await bot.send_message(chat_id=ini_id, text=f'Через 5 минут начнётся ивент {title}, '
                                                        'ваша ссылка на зум в сообщении ниже.\n'
                                                        'После окончания конференции вы можете '
                                                        'возобновить её по этой же ссылке.')
            await bot.send_message(chat_id=ini_id, text=f'{start_url}')
            for user_id in participant_list:
                await bot.send_message(chat_id=user_id, text=f'Через 5 минут начнётся ивент {title}, '
                                                             'ваша ссылка на зум в сообщении ниже.\n'
                                                             'После окончания конференции вы можете '
                                                             'возобновить её по этой же ссылке.')
                await bot.send_message(chat_id=user_id,
                                       text=join_url)
                await sleep(0.3)
                logger.info('Пошла рассылочка')
        else:
            logger.info('По данному ивенту нет участников')
    except Exception as err:
        logger.info(f'{err}')
