import datetime
import logging
import random
from asyncio import sleep

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from connecting_bot.my_bot.bot_spec import bot, scheduler
from connecting_bot.my_bot.db.db_commands import get_text, get_users, get_text_for_participants, \
    get_participants, get_ini_id, delete_initiator_event
from connecting_bot.my_bot.zoom.create_meeting import create_meeting_data
from connecting_bot.my_bot.zoom.delete_meeting import delete_meeting_data


# from connecting_bot.my_bot.keyboards.initiator_kb import add_url


# рассылка
# @dp.message_handler(IsPrivateMsg(), state='*')
async def msg_send_all(callback: types.CallbackQuery, event_id):
    text = get_text(event_id)
    users = get_users(event_id)
    ikb1 = InlineKeyboardButton('Принять участие', callback_data=f'sign_up_{event_id}')
    ikb2 = InlineKeyboardButton('Отказаться', callback_data='sign_up_0')
    ikm = InlineKeyboardMarkup().add(ikb1).add(ikb2)
    if users != None:
        for user_id in users:
            try:
                bot = callback.bot
                await bot.send_message(chat_id=user_id,
                                       text=text,
                                       reply_markup=ikm)
                await sleep(0.3)
            except Exception:
                pass
    else:
        logging.info(f'По ивенту {event_id} нет подходящих под рассылку юзеров')


# отправка напоминания
# @dp.message_handler(IsPrivateMsg(), state='*')
async def send_reminder(event_id, ini_id, title, date):
    text = get_text_for_participants(event_id)
    participant_list = get_participants(event_id)
    if text and participant_list:
        for user_id in participant_list:
            try:
                await bot.send_message(chat_id=user_id,
                                       text=text)
                await sleep(0.3)
                logging.info('Пошла рассылочка')
            except Exception:
                pass


    else:
        logging.info('Не найдено событие или нет участников. Напоминание не отправлено')
    await bot.send_message(chat_id=ini_id,
                           text=f'Через 6 часов состоится событие {title}, '
                                f'За 5 минут до события Вам придёт ссылка-приглашение.')
    dt = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    date_check = dt - datetime.timedelta(seconds=45)

    scheduler.add_job(func=check_availability_participants, trigger='date', run_date=date_check,
                      kwargs={'event_id': int(event_id), 'ini_id': ini_id, 'title': title},
                      timezone='Europe/Moscow')
    date_send = dt - datetime.timedelta(seconds=random.choice(range(27, 32)))
    scheduler.add_job(func=send_url_to_users, trigger='date', run_date=date_send,
                      kwargs={'event_id': int(event_id), 'ini_id': ini_id, 'title': title},
                      timezone='Europe/Moscow')

# проверка, есть ли участники по ивенту
async def check_availability_participants(event_id, ini_id, title):
    list_of_participants = get_participants(event_id)
    if list_of_participants:
        logging.info('Всё идёт по плану')
        pass
    else:
        await bot.send_message(chat_id=ini_id,
                               text=f'По вашему ивенту {title} нет участников,\n'
                                    f'Галя, ОТМЕНА!')
        delete_initiator_event(ini_id, event_id)

# # сообщение инициатору, запрос на ссылку в зум
# async def request_to_initiator(event_id, ini_id, title):
#     start_url, join_url, meeting_id = create_meeting_data(title, datetime.datetime.now())
#     scheduler.add_job(func=delete_meeting_data, trigger='date',
#                       run_date=datetime.datetime.now() + datetime.timedelta(minutes=1),
#                       kwargs={'id': meeting_id})
#     await bot.send_message(chat_id=ini_id, text=f'Через 5 минут начнётся ивент {title}, '
#                                                  'ваша ссылка на зум в сообщении ниже')
#     await bot.send_message(chat_id=ini_id, text=f'{start_url}')
#     await send_url_to_users(event_id, title, join_url)

# отправляем ссылку инициатору и участникам
async def send_url_to_users(event_id, title, ini_id):
    participant_list = get_participants(event_id)
    if participant_list:
        run = datetime.datetime.now() + datetime.timedelta(minutes=1)
        dttt = str(run.strftime('%Y-%m-%d %H:%M:%S'))
        start_url, join_url, meeting_id = create_meeting_data(title, dttt)
        scheduler.add_job(func=delete_meeting_data, trigger='date',
                          run_date=run,
                          kwargs={'meeting_id': meeting_id})
        await bot.send_message(chat_id=ini_id, text=f'Через 5 минут начнётся ивент {title}, '
                                                    'ваша ссылка на зум в сообщении ниже')
        await bot.send_message(chat_id=ini_id, text=f'{start_url}')
        for user_id in participant_list:
            try:
                await bot.send_message(chat_id=user_id, text=f'Через 5 минут начнётся ивент {title}, '
                                                            'ваша ссылка на зум в сообщении ниже')
                await bot.send_message(chat_id=user_id,
                                       text=join_url)
                await sleep(0.3)
                logging.info('Пошла рассылочка')
            except Exception:
                pass
    else:
        logging.info('По данному ивенту нет участников')