import logging

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData

from connecting_bot.my_bot.db.db_commands import my_events, get_categories_list, show_ini_events, categories_list, \
    get_dict_events

callback_data = CallbackData('user_id', 'action')

def initiator_start_kb() -> ReplyKeyboardMarkup:
    kb = KeyboardButton(text='Подписаться на рассылку')
    kb1 = KeyboardButton(text='Отписаться от рассылки')
    kb2 = KeyboardButton(text='Уже участвую')
    kb3 = KeyboardButton(text='Могу поучаствовать')
    kb4 = KeyboardButton(text='Мои ивенты')
    kb5 = KeyboardButton(text='Добавить ивент')

    keyboard = ReplyKeyboardMarkup().row(kb, kb1).row(kb2, kb3).row(kb4, kb5)
    return keyboard

def ikb_initiator() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Добавить событие', callback_data='add_event')],
        [InlineKeyboardButton('Посмотреть список событий', callback_data='show_events')]
    ])
    return kb

def confirm_ikb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Опубликовать событие', callback_data='add_confirm')],
        [InlineKeyboardButton('Заполнить заново', callback_data='add_event')],
    ])
    return kb

def initiator_delete_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Удалить событие', callback_data='delete_my_event')],
        [InlineKeyboardButton('Вернуться назад', callback_data='return_to_my_event')]
    ])
    return kb

def initiator_refuse_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Отказаться от участия в событии', callback_data='i_refuse_event')],
        [InlineKeyboardButton('Назад к списку событий', callback_data='i_return_back')]
    ])
    return kb

def ini_agree_or_disagree():
    kb = InlineKeyboardMarkup(inline_keyboard=[
            [KeyboardButton(text="Принять участие", callback_data='ini_agree')],
            [KeyboardButton(text="Отказаться", callback_data='ini_disagree')]
        ])
    return kb

def ini_main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
            [KeyboardButton(text="Главное меню", callback_data='main_menu_custom')]
        ])
    return kb


def ikb13(id) -> InlineKeyboardMarkup:
    events_id_title = my_events(id)
    buttons_list = list()
    for key, value in events_id_title.items():
        buttons_list.append([InlineKeyboardButton(text=value,
                                                  callback_data='even_' + str(key))])
    buttons_list.append([InlineKeyboardButton(text='Назад',
                                              callback_data='even_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    logging.info('oooooooooooooooooooooooooooooooooooo')
    logging.info(f'{buttons_list}')
    return kb_events


def ikb12(id) -> InlineKeyboardMarkup:
    buttons_list = list()
    categories_list = get_categories_list(id)
    for each in categories_list:
        buttons_list.append([InlineKeyboardButton(text=each,
                                                  callback_data='cat_' + str(each))])
        buttons_list.append([InlineKeyboardButton(text='Назад',
                                                  callback_data='cat_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events


def ikb11(id, category) -> InlineKeyboardMarkup:
    buttons_list = list()
    buttons_dict = get_dict_events(id, category)
    for key, value in buttons_dict.items():
        buttons_list.append([InlineKeyboardButton(text=str(key),
                                                  callback_data=str(value))])
    buttons_list.append([InlineKeyboardButton(text='К списку категорий',
                                              callback_data='event_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events


def ikb14(id) -> InlineKeyboardMarkup:
    events_id_title = show_ini_events(id)
    buttons_list = list()
    for key, value in events_id_title.items():
        buttons_list.append([InlineKeyboardButton(text=value,
                                                  callback_data='myev_' + str(key))])
    buttons_list.append([InlineKeyboardButton(text='Назад',
                                              callback_data='myev_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events


def ikb16() -> InlineKeyboardMarkup:
    buttons_list = list()
    categories_list_title = categories_list()
    for each in categories_list_title:
        buttons_list.append([InlineKeyboardButton(text=each,
                                                  callback_data='categ_' + str(each))])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events
