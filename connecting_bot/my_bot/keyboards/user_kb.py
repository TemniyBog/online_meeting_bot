from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData
from loguru import logger

callback_data = CallbackData('user_id', 'action')


def kb20() -> ReplyKeyboardMarkup:
    kb = KeyboardButton(text='Подписаться на рассылку')
    kb1 = KeyboardButton(text='Отписаться от рассылки')
    kb2 = KeyboardButton(text='Уже участвую')
    kb3 = KeyboardButton(text='Могу поучаствовать')
    kb4 = KeyboardButton(text='Установить часовой пояс')

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).row(kb, kb1).row(kb2, kb3).row(kb4)
    return keyboard


# отказаться от участия в событии
def kb24() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Отказаться от участия в событии', callback_data='refuse_event')],
        [InlineKeyboardButton('Назад к списку событий', callback_data='return_back')]
    ])
    return kb


def kb25():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [KeyboardButton(text="Принять участие", callback_data='agree')],
        [KeyboardButton(text="Отказаться", callback_data='disagree')]
    ])
    return kb


def kb23(events_id_title) -> InlineKeyboardMarkup:
    buttons_list = list()
    for key, value in events_id_title.items():
        buttons_list.append([InlineKeyboardButton(text=value,
                                                  callback_data='ev_' + str(key))])
    buttons_list.append([InlineKeyboardButton(text='Назад',
                                              callback_data='ev_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    logger.info(f'{buttons_list}')
    return kb_events


def kb22(categories_list) -> InlineKeyboardMarkup:
    buttons_list = list()
    for each in categories_list:
        buttons_list.append([InlineKeyboardButton(text=each,
                                                  callback_data='category_' + str(each))])
    buttons_list.append([InlineKeyboardButton(text='Назад',
                                              callback_data='category_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events


def kb21(buttons_dict) -> InlineKeyboardMarkup:
    buttons_list = list()
    for key, value in buttons_dict.items():
        buttons_list.append([InlineKeyboardButton(text=str(key),
                                                  callback_data=str(value))])
    buttons_list.append([InlineKeyboardButton(text='К списку категорий',
                                              callback_data='usevent_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events


def ikm(event_id) -> InlineKeyboardMarkup:
    ikb1 = InlineKeyboardButton('Принять участие', callback_data=f'sign_up_{event_id}')
    ikb2 = InlineKeyboardButton('Отказаться', callback_data='sign_up_0')
    kb = InlineKeyboardMarkup().add(ikb1).add(ikb2)
    return kb
