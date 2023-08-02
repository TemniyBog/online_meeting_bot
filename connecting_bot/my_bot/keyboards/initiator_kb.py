from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData

callback_data = CallbackData('user_id', 'action')


def kb10() -> ReplyKeyboardMarkup:
    kb = KeyboardButton(text='Подписаться на рассылку')
    kb1 = KeyboardButton(text='Отписаться от рассылки')
    kb2 = KeyboardButton(text='Уже участвую')
    kb3 = KeyboardButton(text='Могу поучаствовать')
    kb4 = KeyboardButton(text='Мои ивенты')
    kb5 = KeyboardButton(text='Добавить ивент')
    kb6 = KeyboardButton(text='Установить часовой пояс')

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True).row(kb, kb1).row(kb2, kb3).row(kb4, kb5).row(kb6)
    return keyboard


def kb15() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Опубликовать событие', callback_data='add_confirm')],
        [InlineKeyboardButton('Заполнить заново', callback_data='add_event')],
    ])
    return kb


def kb17() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Удалить событие', callback_data='delete_my_event')],
        [InlineKeyboardButton('Вернуться назад', callback_data='return_to_my_event')]
    ])
    return kb


def kb18() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Отказаться от участия в событии', callback_data='i_refuse_event')],
        [InlineKeyboardButton('Назад к списку событий', callback_data='i_return_back')]
    ])
    return kb


def kb19():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [KeyboardButton(text="Принять участие", callback_data='ini_agree')],
        [KeyboardButton(text="Отказаться", callback_data='ini_disagree')]
    ])
    return kb


def kb13(events_id_title) -> InlineKeyboardMarkup:
    buttons_list = list()
    for key, value in events_id_title.items():
        buttons_list.append([InlineKeyboardButton(text=value,
                                                  callback_data='even_' + str(key))])
    buttons_list.append([InlineKeyboardButton(text='Назад',
                                              callback_data='even_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events


def kb12(categories_list) -> InlineKeyboardMarkup:
    buttons_list = list()
    for each in categories_list:
        buttons_list.append([InlineKeyboardButton(text=each,
                                                  callback_data='cat_' + str(each))])
    buttons_list.append([InlineKeyboardButton(text='Назад',
                                              callback_data='cat_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events


def kb11(buttons_dict) -> InlineKeyboardMarkup:
    buttons_list = list()
    for key, value in buttons_dict.items():
        buttons_list.append([InlineKeyboardButton(text=str(key),
                                                  callback_data=str(value))])
    buttons_list.append([InlineKeyboardButton(text='К списку категорий',
                                              callback_data='event_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events


def kb14(events_id_title) -> InlineKeyboardMarkup:
    buttons_list = list()
    for key, value in events_id_title.items():
        buttons_list.append([InlineKeyboardButton(text=value,
                                                  callback_data='myev_' + str(key))])
    buttons_list.append([InlineKeyboardButton(text='Назад',
                                              callback_data='myev_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events


def kb16(categories_list_title) -> InlineKeyboardMarkup:
    buttons_list = list()
    for each in categories_list_title:
        buttons_list.append([InlineKeyboardButton(text=each,
                                                  callback_data='categ_' + str(each))])
    buttons_list.append([InlineKeyboardButton(text='Вернуться в главное меню',
                                              callback_data='categ_0')])
    kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
    return kb_events


def kb00():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [KeyboardButton(text="Главное меню", callback_data='main_menu_custom')]
    ])
    return kb
