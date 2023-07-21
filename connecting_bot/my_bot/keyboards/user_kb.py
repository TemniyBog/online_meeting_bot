import logging

from aiogram import types

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData

from connecting_bot.my_bot.db.db_commands import my_events, get_categories_list, get_user_dict_events

callback_data = CallbackData('user_id', 'action')

def subscribe() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Подписаться на рассылку', callback_data='add_new_user')],
        [InlineKeyboardButton('Отписаться от рассылки', callback_data='delete_user')],
    ])
    return kb

def user_start_kb() -> ReplyKeyboardMarkup:
    kb = KeyboardButton(text='Подписаться на рассылку')
    kb1 = KeyboardButton(text='Отписаться от рассылки')
    kb2 = KeyboardButton(text='Уже участвую')
    kb3 = KeyboardButton(text='Могу поучаствовать')

    keyboard = ReplyKeyboardMarkup().row(kb, kb1).row(kb2, kb3)
    return keyboard

# отказаться от участия в событии
def user_refuse_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Отказаться от участия в событии', callback_data='refuse_event')],
        [InlineKeyboardButton('Назад к списку событий', callback_data='return_back')]
    ])
    return kb

def agree_or_disagree():
    kb = InlineKeyboardMarkup(inline_keyboard=[
            [KeyboardButton(text="Принять участие", callback_data='agree')],
            [KeyboardButton(text="Отказаться", callback_data='disagree')]
        ])
    return kb

def get_subscribe() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Подписаться на рассылку', callback_data='add_new_user')]
    ])
    return kb

def not_subscribe() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Отписаться от рассылки', callback_data='delete_user')]
    ])
    return kb

def ikb1() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Принять участие в событии', callback_data='sign_up')],
        [InlineKeyboardButton('Отклонить событие', callback_data='not_sign_up')]
    ])
    return kb


def ikb23(id) -> InlineKeyboardMarkup:
    events_id_title = my_events(id)
    buttons_list = list()
    for key, value in events_id_title.items():
        buttons_list.append([InlineKeyboardButton(text=value,
                                                  callback_data='ev_' + str(key))])
    buttons_list.append([InlineKeyboardButton(text='Назад',
                                              callback_data='ev_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    logging.info(f'{buttons_list}')
    return kb_events


def ikb22(id) -> InlineKeyboardMarkup:
    categories_list = get_categories_list(id)
    buttons_list = list()
    for each in categories_list:
        buttons_list.append([InlineKeyboardButton(text=each,
                                                  callback_data='category_' + str(each))])
    buttons_list.append([InlineKeyboardButton(text='Назад',
                                              callback_data='category_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events


def ikb21(id, category) -> InlineKeyboardMarkup:
    buttons_list = list()
    buttons_dict = get_user_dict_events(id, category)
    for key, value in buttons_dict.items():
        buttons_list.append([InlineKeyboardButton(text=str(key),
                                                  callback_data=str(value))])
    buttons_list.append([InlineKeyboardButton(text='К списку категорий',
                                              callback_data='usevent_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events