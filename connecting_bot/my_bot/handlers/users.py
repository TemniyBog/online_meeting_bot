import asyncio
import logging

from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from connecting_bot.my_bot.bot_spec import bot
from connecting_bot.my_bot.db.db_commands import subscribe_user, delete_user, get_dict_events, get_text, \
    get_categories_list, register_user, my_events, refuse_user, check_count_of_participants, add_participant, \
    get_user_dict_events
from connecting_bot.my_bot.filters.filters import IsPrivateMsg, IsPrivateCb
from connecting_bot.my_bot.keyboards.user_kb import user_start_kb, user_refuse_kb, agree_or_disagree, ikb23, ikb22, \
    ikb21
from connecting_bot.my_bot.states.user_state import UserState

# старт
async def process_start_command(message: types.Message, state: FSMContext):
    register_user(message)
    await message.answer('Привет!\nВыберите пункт', reply_markup=user_start_kb())
    await UserState.wait_for.set()

# главное меню
async def user_msg_main_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Выберите пункт', reply_markup=user_start_kb())
    await UserState.wait_for.set()

# command = help
async def user_help(message: types.Message, state: FSMContext):
    await message.answer('По всем интересующим Вас вопросам, а также в случае непредвиденных '
                         'ситуаций пишите в телеграм разрабочикам - @M1sterJack')

# оформить подписку юзеру
# @dp.callback_query_handler(IsPrivateCb(), text='подписаться на рассылку', state=UserState.wait_for_choose)
async def user_msg_add_new_user(message: types.Message, state: FSMContext):
    subscribe_user(message.from_user.id)
    await message.answer(text="Вы подписаны на рассылку! Не включайте мьют, "
                         "здесь не будет рекламы)")
    await UserState.in_game.set()

# отписать юзера
# @dp.callback_query_handler(IsPrivateCb(), text='отписаться от рассылки', state=UserState.wait_for_choose)
async def user_msg_delete_user(message: types.Message, state: FSMContext):
    delete_user(message.from_user.id)
    await message.answer(text="Вы отписались от рассылки(")
    logging.info('user')
    await UserState.in_game.set()

# Уже участвую
# показываем события, в которых юзер участвует
async def user_my_list_events(message: types.Message, state: FSMContext):
    if my_events(message.chat.id):
        await bot.send_message(chat_id=message.chat.id,
                               text='Ищем события...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await bot.send_message(chat_id=message.chat.id,
                               text='События, в которых вы участвуете',
                               reply_markup=ikb23(message.chat.id))
        await UserState.show_list_events.set()
    else:
        await bot.send_message(chat_id=message.chat.id,
                               text='Вы пока не участвуете ни в одном событии',
                               reply_markup=user_start_kb())
        await UserState.wait_for.set()

# прокладка для коллбека
async def beetwen_user_my_list_events(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await user_my_list_events(callback.message, state)
    await UserState.in_game.set()

# async def my_list_events(message: types.Message, state: FSMContext):
#     events_id_title = my_events(message.from_user.id)
#     buttons_list = list()
#     if events_id_title:
#         def ikb3() -> InlineKeyboardMarkup:
#             for key, value in events_id_title.items():
#                 buttons_list.append([InlineKeyboardButton(text=value,
#                                                           callback_data='ev_' + str(key))])
#             buttons_list.append([InlineKeyboardButton(text='Назад',
#                                                       callback_data='0')])
#             kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
#             return kb_events
#
#         await message.answer(text='Ищем события...', reply_markup=ReplyKeyboardRemove())
#         await asyncio.sleep(1)
#         await message.answer('События, в которых вы участвуете',
#                                       reply_markup=ikb3())
#         await UserState.show_list_events.set()
#     else:
#         await message.answer('Вы пока не участвуете ни в одном событии',
#                                       reply_markup=user_start_kb())
#         await UserState.wait_for.set()

# выбрал событие
async def user_choose_my_events(callback: types.CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split('_')[-1])
    logging.info('yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy')
    logging.info(f'{event_id}')
    bot = callback.bot
    await callback.message.delete()
    if event_id == 0:
        await state.finish()
        await callback.message.answer('Выберите пункт', reply_markup=user_start_kb())
        await UserState.in_game.set()
    else:
        text = get_text(event_id)
        await state.update_data(EVEN_ID=event_id) # сохраняем данные
        await bot.send_message(chat_id=callback.from_user.id, text=text,
                               reply_markup=user_refuse_kb())
        await UserState.make_choose.set()

# async def choose_my_events(callback: types.CallbackQuery, state: FSMContext):
#     event_id = callback.data.split('_')[-1]
#     await callback.message.delete()
#     if event_id == 0:
#         await callback.message.answer(text='Выберите пункт',
#                                       reply_markup=user_start_kb())
#         await UserState.wait_for.set()
#     else:
#         text = get_text(int(event_id))
#         await state.update_data(EV_ID=event_id) # сохраняем данные
#         await callback.message.answer(text=text,
#                                       reply_markup=user_refuse_kb())
#         await UserState.make_choose.set()



# отказывается от участия
async def refuser_my_events(callback: types.CallbackQuery, state: FSMContext):
    event_id = await state.get_data('EVEN_ID') # получаем данные
    logging.info(f'{event_id["EVEN_ID"]}')
    bot = callback.bot
    await callback.message.delete()
    if refuse_user(callback.from_user.id, event_id['EVEN_ID']):
        logging.info('check1')
        await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии')
        await user_my_list_events(callback.message, state)
        await state.reset_data()
        await UserState.in_game.set()
    else:
        await bot.send_message(chat_id=callback.from_user.id,
                               text='Вы не были удалены из события, '
                                    'обратитесь к разработикам - @M1sterJack')
        await state.reset_data()
        await user_my_list_events(callback.message, state)
        await UserState.in_game.set()
        logging.info('Не удалось удалить участника')


# async def refuser_my_events(callback: types.CallbackQuery, state: FSMContext):
#     event_id = state.get_data('EV_ID') # получаем данные
#     await callback.message.delete()
#     if refuse_user(callback.from_user.id, event_id):
#         await callback.message.answer(text='Вы отказались от участия в событии')
#         await my_list_events(callback.message, state)
#         await state.reset_data()
#         await UserState.in_game.set()
#     else:
#         await callback.message.answer(text='Вы не были удалены из события, '
#                                            'обратитесь к разработикам - @M1sterJack')
#         await state.reset_data()
#         await my_list_events(callback.message, state)
#         await UserState.in_game.set()
#         logging.info('Не удалось удалить участника')

# назад к списку категорий
async def return_cat(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await user_my_list_events(callback.message, state)
    await UserState.show_categories.set()

# Могу поучаствовать
# показываем категории, если они есть
async def user_all_category_list(message: types.Message, state: FSMContext):
    if get_categories_list(message.chat.id):
        await message.answer(text='Ищем события...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await message.answer(text='Выберите категорию',
                             reply_markup=ikb22(message.from_user.id))
        await UserState.show_categories.set()
    else:
        await bot.send_message(chat_id=message.chat.id, text='Пока нет событий',
                               reply_markup=user_start_kb())
        await UserState.wait_for.set()

# async def all_category_list(message: types.Message, state: FSMContext):
#     buttons_list = list()
#     if get_categories_list(message.chat.id):
#         categories_list = get_categories_list(message.chat.id)
#         def ikb2() -> InlineKeyboardMarkup:
#             for x in range(len(categories_list)):
#                 buttons_list.append([InlineKeyboardButton(text=categories_list[x],
#                                                           callback_data='category_' +
#                                                                         str(categories_list[x]))])
#             kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
#             return kb_events
#         await message.answer(text='Посмотрим, есть ли события...', reply_markup=ReplyKeyboardRemove())
#         await asyncio.sleep(1)
#         await message.answer(text='Выберите категорию',
#                                       reply_markup=ikb2())
#         await UserState.show_categories.set()
#     else:
#         await message.answer(text='Пока нет событий',
#                                       reply_markup=user_start_kb())
#         await UserState.wait_for.set()

# показываем ивенты по выбранной категории
async def user_all_list_events(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split('_')[-1]
    await callback.message.delete()
    logging.info(f'{await state.get_state()}')
    if category == '0':
        bot = callback.bot
        await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт',
                               reply_markup=user_start_kb())
        await UserState.wait_for.set()
    else:
        bot = callback.bot
        if get_user_dict_events(callback.from_user.id, category):
            await bot.send_message(chat_id=callback.from_user.id, text='Выберите событие',
                                   reply_markup=ikb21(callback.from_user.id, category))
            await UserState.show_events.set()
        else:
            await bot.send_message(chat_id=callback.from_user.id, text='Пока нет событий по этой категории')
            await user_all_category_list(callback.message, state)
            await UserState.show_categories.set()

# async def all_list_events(callback: types.CallbackQuery, state: FSMContext):
#     category = callback.data.split('_')[-1]
#     await callback.message.delete()
#     if get_dict_events(callback.from_user.id, category):
#         buttons_dict = dict()
#         buttons_list = list()
#         val_list = list()
#         key_list = list()
#         buttons_dict = get_dict_events(callback.from_user.id)
#
#         def ikb1() -> InlineKeyboardMarkup:
#             for key, value in buttons_dict.items():
#                 logging.info(f'checkkkkkkkkk {key}    {value}')
#                 kb_events = InlineKeyboardMarkup()
#                 val = str(value)
#                 val = val.replace("\n", "")
#                 val_list.append(val)
#                 key_list.append(str(key))
#             for x in range(len(buttons_dict)):
#                 buttons_list.append([InlineKeyboardButton(text=val_list[x],
#                                                           callback_data=key_list[x])])
#             kb_events = InlineKeyboardMarkup(inline_keyboard=buttons_list)
#             return kb_events
#         await callback.message.answer(text='Выберите событие',
#                                       reply_markup=ikb1())
#         await UserState.show_events.set()
#     else:
#         await callback.message.answer('Пока нет событий по этой категории')
#         await user_all_category_list(callback.message, state)
#         await UserState.in_game.set()

# выбирает одно из событий
# @dp.callback_query_handler(IsPrivateCb(), lambda callback: callback.data.startswith('event_'),
#                            state=InitiatorState.events)
async def cb_user_choose_events(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split('_')[-1]
    await callback.message.delete()
    if int(event_id) == 0:
        await user_all_category_list(callback.message, state)
        await UserState.in_game.set()
    else:
        text = get_text(event_id)
        await state.update_data(usevent_id=event_id)
        bot = callback.bot
        await bot.send_message(chat_id=callback.from_user.id, text=text,
                               reply_markup=agree_or_disagree())
        await UserState.agree_disagree.set()

# async def cb_choose_events(callback: types.CallbackQuery, state: FSMContext):
#     event_id = callback.data.split('_')[-1]
#     await callback.message.delete()
#     text = get_text(event_id)
#     await state.update_data(event_id=event_id)
#     await callback.message.answer(text=text,
#                                   reply_markup=agree_or_disagree())
#     await UserState.agree_disagree.set()


# участвует в событии
# @dp.callback_query_handler(IsPrivateCb(), text='agree', state=InitiatorState.agree_disagree)
async def cb_user_agree(callback: types.CallbackQuery, state: FSMContext):
    bot = callback.bot
    await callback.message.delete()
    async with state.proxy() as data:
        event_id = data['usevent_id']
    if check_count_of_participants(event_id):
        if add_participant(callback.from_user.id, event_id):
            await bot.send_message(chat_id=callback.from_user.id,
                                   text='Вам придёт ссылка-приглашение на событие, ожидайте')
            await state.reset_data()
            await UserState.in_game.set()
            await user_all_category_list(callback.message, state)
        else:
            await bot.send_message(chat_id=callback.from_user.id,
                                   text='Упс! Мы не смогли Вас добавить в участники события')
            await state.reset_data()
            await UserState.in_game.set()
            await user_all_category_list(callback.message, state)
    else:
        await state.reset_data()
        await bot.send_message(chat_id=callback.from_user.id,
                               text="К сожалению, на это мероприятие все места уже заняты, "
                                     "ожидайте объявление нового события")
        await state.reset_data()
        await UserState.in_game.set()
        await user_all_category_list(callback.message, state)

# async def cb_agree(callback: types.CallbackQuery, state: FSMContext):
#     await callback.message.delete()
#     async with state.proxy() as data:
#         event_id = data['event_id']
#     if check_count_of_participants(event_id):
#         add_participant(callback.from_user.id, event_id)
#         await callback.message.answer('Вам придёт ссылка=приглашение на событие, ожидайте')
#         await UserState.in_game.set()
#         await all_category_list(callback.message, state)
#         await state.reset_data()
#     else:
#         await state.reset_data()
#         await callback.message.answer("К сожалению, на это мероприятие все места уже заняты, "
#                                       "ожидайте объявление нового события")
#         await UserState.in_game.set()
#         await all_category_list(callback.message, state)
#         await state.reset_data()


# отказывается участвовать
# @dp.callback_query_handler(IsPrivateCb(), text='disagree', state=InitiatorState.agree_disagree)
async def cb_user_disagree(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.finish()
    bot = callback.bot
    await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии!')
    await UserState.in_game.set()
    await user_all_category_list(callback.message, state)

# async def cb_disagree(callback: types.CallbackQuery, state: FSMContext):
#     await callback.message.delete()
#     await state.finish()
#     await callback.message.answer(text='Вы отказались от участия в событии!')
#     await UserState.in_game.set()
#     await all_category_list(callback.message, state)

# ответил на рассылку Принять участие или 0 = Отказаться
async def answer_to_mailing(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split('_')[-1]
    await callback.message.delete()
    if int(event_id) == 0:
        pass
    else:
        bot = callback.bot
        if add_participant(callback.from_user.id, event_id):
            await bot.send_message(chat_id=callback.from_user.id,
                                   text='Вам придёт ссылка-приглашение на событие, ожидайте')
        else:
            await bot.send_message(chat_id=callback.from_user.id,
                                   text='Упс! Мы не смогли Вас добавить в участники события')


def register_handlers_users(dp: Dispatcher):
    dp.register_message_handler(process_start_command, IsPrivateMsg(), commands=['start'], state=None)
    dp.register_message_handler(user_msg_main_menu, IsPrivateMsg(), commands=['main_menu'], state='*')
    dp.register_message_handler(user_help, IsPrivateMsg(), commands=['help'], state='*')

    dp.register_message_handler(user_msg_add_new_user,
                                text='Подписаться на рассылку', state='*')

    dp.register_message_handler(user_msg_delete_user, IsPrivateMsg(),
                                text='Отписаться от рассылки', state='*')
    #
    dp.register_message_handler(user_my_list_events, text='Уже участвую', state='*')
    dp.register_callback_query_handler(user_choose_my_events, IsPrivateCb(),
                                       lambda callback: callback.data.startswith('ev_'),
                                       state='*')
    dp.register_callback_query_handler(refuser_my_events, IsPrivateCb(),
                                       text='refuse_event',
                                       state=UserState.make_choose)
    dp.register_callback_query_handler(beetwen_user_my_list_events, IsPrivateCb(),
                                       text='return_back',
                                       state=UserState.make_choose)

    dp.register_message_handler(user_all_category_list, text='Могу поучаствовать', state='*')
    dp.register_callback_query_handler(user_all_list_events, IsPrivateCb(),
                                       lambda callback: callback.data.startswith('category_'),
                                       state='*')
    dp.register_callback_query_handler(cb_user_choose_events, IsPrivateCb(),
                                       lambda callback: callback.data.startswith('usevent_'),
                                       state=UserState.show_events)
    dp.register_callback_query_handler(cb_user_agree, IsPrivateCb(), text='agree',
                                       state=UserState.agree_disagree)
    dp.register_callback_query_handler(cb_user_disagree, IsPrivateCb(), text='disagree',
                                       state=UserState.agree_disagree)
    dp.register_callback_query_handler(answer_to_mailing, IsPrivateCb(),
                                       lambda callback: callback.data.startswith('sign_up_'),
                                       state='*')
