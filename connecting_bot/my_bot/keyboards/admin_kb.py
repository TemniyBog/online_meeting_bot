import logging

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData

from connecting_bot.my_bot.db.db_commands import my_events, get_categories_list, get_dict_events

callback_data = CallbackData('user_id', 'action')

def kb0() -> ReplyKeyboardMarkup:
    kb = KeyboardButton(text='Подписаться на рассылку')
    kb1 = KeyboardButton(text='Отписаться от рассылки')
    kb2 = KeyboardButton(text='Уже участвую')
    kb3 = KeyboardButton(text='Могу поучаствовать')
    kb4 = KeyboardButton(text='Добавить инициатора')
    kb5 = KeyboardButton(text='Добавить категорию')

    keyboard = ReplyKeyboardMarkup().row(kb, kb1).row(kb2, kb3).row(kb4, kb5)
    return keyboard

def kb1() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Отказаться от участия в событии', callback_data='adm_refuse_event')],
        [InlineKeyboardButton('Назад к списку событий', callback_data='adm_return_back')]
    ])
    return kb

def kb5():
    kb = InlineKeyboardMarkup(inline_keyboard=[
            [KeyboardButton(text="Принять участие", callback_data='adm_agree')],
            [KeyboardButton(text="Отказаться", callback_data='adm_disagree')]
        ])
    return kb


def kb3(id) -> InlineKeyboardMarkup:
    events_id_title = my_events(id)
    buttons_list = list()
    for key, value in events_id_title.items():
        buttons_list.append([InlineKeyboardButton(text=value,
                                                  callback_data='admeven_' + str(key))])
    buttons_list.append([InlineKeyboardButton(text='Назад',
                                              callback_data='admeven_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    logging.info('oooooooooooooooooooooooooooooooooooo')
    logging.info(f'{buttons_list}')
    return kb_events


def kb2(id) -> InlineKeyboardMarkup:
    buttons_list = list()
    categories_list = get_categories_list(id)
    for each in categories_list:
        buttons_list.append([InlineKeyboardButton(text=each,
                                                  callback_data='admcat_' + str(each))])
    buttons_list.append([InlineKeyboardButton(text='Назад',
                                              callback_data='admcat_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events


def kb4(id, category) -> InlineKeyboardMarkup:
    buttons_list = list()
    buttons_dict = get_dict_events(id, category)
    for key, value in buttons_dict.items():
        buttons_list.append([InlineKeyboardButton(text=str(key),
                                                  callback_data=str(value))])
    buttons_list.append([InlineKeyboardButton(text='К списку категорий',
                                              callback_data='event_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events