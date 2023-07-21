import asyncio
import datetime
import logging

from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from connecting_bot.my_bot.bot_spec import scheduler, bot
from connecting_bot.my_bot.db.db_commands import save_event, \
    check_time, check_date, get_text, add_participant, check_count_of_participants, \
    get_dict_events, register_user, subscribe_user, delete_user, my_events, refuse_user, \
    get_categories_list, show_ini_events, delete_initiator_event, categories_list
from connecting_bot.my_bot.filters.filters import IsPrivateCb, IsPrivateMsg, IsInitiatorMsgFilter
from connecting_bot.my_bot.keyboards.initiator_kb import confirm_ikb, initiator_start_kb, \
    initiator_delete_kb, initiator_refuse_kb, ini_agree_or_disagree, ikb13, ikb12, ikb11, ikb14, ikb16
from connecting_bot.my_bot.misc.functions import msg_send_all, send_reminder
from connecting_bot.my_bot.states.initiator_state import InitiatorState


# старт инициаторы
async def start_command(message: types.Message, state: FSMContext):
    register_user(message)
    await message.answer(text="Привет!\nВыберите пункт",
                         reply_markup=initiator_start_kb())
    await InitiatorState.wait_for.set()

# command = main menu
async def msg_main_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Выберите пункт', reply_markup=initiator_start_kb())
    await InitiatorState.wait_for.set()

# command = help
async def ini_help(message: types.Message, state: FSMContext):
    await message.answer('По всем интересующим Вас вопросам, а также в случае непредвиденных '
                         'ситуаций пишите в телеграм разрабочикам - @M1sterJack')

# Подписаться
# оформить подписку юзеру
# @dp.callback_query_handler(IsPrivateCb(), text='подписаться на рассылку', state=UserState.wait_for_choose)
async def msg_add_new_user(message: types.Message, state: FSMContext):
    subscribe_user(message.from_user.id)
    await message.answer(text="Вы подписаны на рассылку! Не включайте мьют, "
                              "здесь не будет рекламы)")
    await InitiatorState.in_game.set()

# Отписаться
# отписать юзера
# @dp.callback_query_handler(IsPrivateCb(), text='отписаться от рассылки', state=UserState.wait_for_choose)
async def msg_delete_user(message: types.Message, state: FSMContext):
    delete_user(message.from_user.id)
    await message.answer(text="Вы отписались от рассылки(")
    logging.info('initiator')
    await InitiatorState.in_game.set()

# Уже участвую
# показываем события, в которых юзер участвует
async def my_list_events(message: types.Message, state: FSMContext):
    if my_events(message.chat.id):
        await bot.send_message(chat_id=message.chat.id,
                               text='Ищем события...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await bot.send_message(chat_id=message.chat.id,
                               text='События, в которых вы участвуете',
                               reply_markup=ikb13(message.chat.id))
        await InitiatorState.show_list_events.set()
    else:
        await bot.send_message(chat_id=message.chat.id,
                               text='Вы пока не участвуете ни в одном событии',
                               reply_markup=initiator_start_kb())
        await InitiatorState.wait_for.set()

# выбрал событие
async def choose_my_events(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split('_')[-1]
    logging.info('yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy')
    logging.info(f'{event_id}')
    bot = callback.bot
    await callback.message.delete()
    if int(event_id) == 0:
        await state.finish()
        await callback.message.answer('Выберите пункт', reply_markup=initiator_start_kb())
        await InitiatorState.in_game.set()
    else:
        text = get_text(int(event_id))
        await state.update_data(EV_ID=event_id) # сохраняем данные
        await bot.send_message(chat_id=callback.from_user.id, text=text,
                               reply_markup=initiator_refuse_kb())
        await InitiatorState.make_choose.set()

# отказывается от участия
async def refuse_my_events(callback: types.CallbackQuery, state: FSMContext):
    event_id = await state.get_data('EV_ID') # получаем данные
    logging.info(f'{event_id["EV_ID"]}')
    bot = callback.bot
    await callback.message.delete()
    if refuse_user(callback.from_user.id, event_id['EV_ID']):
        logging.info('check1')
        await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии')
        await my_list_events(callback.message, state)
        await state.reset_data()
        await InitiatorState.in_game.set()
    else:
        await bot.send_message(chat_id=callback.from_user.id, text='Вы не были удалены из события, '
                                           'обратитесь к разработикам - @M1sterJack')
        await state.reset_data()
        await my_list_events(callback.message, state)
        await InitiatorState.in_game.set()
        logging.info('Не удалось удалить участника')

# назад к списку категорий
async def return_cat(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await my_list_events(callback.message, state)
    await InitiatorState.show_categories.set()

# Могу поучаствовать
# показываем категории, если они есть
# будет работать только для приватных чатов
async def all_ini_category_list(message: types.Message, state: FSMContext):
    if get_categories_list(message.chat.id):
        await message.answer(text='Ищем события...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await message.answer(text='Выберите категорию',
                             reply_markup=ikb12(message.chat.id))
        await InitiatorState.show_categories.set()
    else:
        await bot.send_message(chat_id=message.chat.id, text='Пока нет событий',
                               reply_markup=initiator_start_kb())
        await InitiatorState.wait_for.set()

# показываем ивенты по выбранной категории
async def all_list_events(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split('_')[-1]
    await callback.message.delete()
    logging.info(f'{await state.get_state()}')
    if category == '0':
        bot = callback.bot
        await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт',
                               reply_markup=initiator_start_kb())
        await InitiatorState.wait_for.set()
    else:
        bot = callback.bot
        if get_dict_events(callback.from_user.id, category):
            await bot.send_message(chat_id=callback.from_user.id, text='Выберите событие',
                                   reply_markup=ikb11(callback.from_user.id, category))
            await InitiatorState.show_events.set()
        else:
            await bot.send_message(chat_id=callback.from_user.id, text='Пока нет событий по этой категории')
            await all_ini_category_list(callback.message, state)
            await InitiatorState.show_categories.set()

# выбирает одно из событий
# @dp.callback_query_handler(IsPrivateCb(), lambda callback: callback.data.startswith('event_'),
#                            state=InitiatorState.events)
async def cb_choose_events(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split('_')[-1]
    await callback.message.delete()
    if int(event_id) == 0:
        await all_ini_category_list(callback.message, state)
        await InitiatorState.in_game.set()
    else:
        text = get_text(event_id)
        await state.update_data(event_id=event_id)
        bot = callback.bot
        await bot.send_message(chat_id=callback.from_user.id, text=text,
                               reply_markup=ini_agree_or_disagree())
        await InitiatorState.agree_disagree.set()


# участвует в событии
# @dp.callback_query_handler(IsPrivateCb(), text='agree', state=InitiatorState.agree_disagree)
async def cb_agree(callback: types.CallbackQuery, state: FSMContext):
    bot = callback.bot
    await callback.message.delete()
    async with state.proxy() as data:
        event_id = data['event_id']
    if check_count_of_participants(event_id):
        if add_participant(callback.from_user.id, event_id):
            await bot.send_message(chat_id=callback.from_user.id,
                                   text='Вам придёт ссылка-приглашение на событие, ожидайте')
            await state.reset_data()
            await InitiatorState.in_game.set()
            await all_ini_category_list(callback.message, state)
        else:
            await bot.send_message(chat_id=callback.from_user.id,
                                   text='Упс! Мы не смогли Вас добавить в участники события')
            await state.reset_data()
            await InitiatorState.in_game.set()
            await all_ini_category_list(callback.message, state)
    else:
        await state.reset_data()
        await bot.send_message(chat_id=callback.from_user.id,
                               text="К сожалению, на это мероприятие все места уже заняты, "
                                     "ожидайте объявление нового события")
        await state.reset_data()
        await InitiatorState.in_game.set()
        await all_ini_category_list(callback.message, state)


# отказывается участвовать
# @dp.callback_query_handler(IsPrivateCb(), text='disagree', state=InitiatorState.agree_disagree)
async def cb_disagree(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.finish()
    bot = callback.bot
    await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии!')
    await InitiatorState.in_game.set()
    await all_ini_category_list(callback.message, state)


# только для инициаторов #################################
# Мои ивенты
# ивенты инициатора, которые он инициировал
async def msg_initiator_events(message: types.Message, state: FSMContext):
    if show_ini_events(message.chat.id):
        await bot.send_message(chat_id=message.chat.id,
                               text='Ищем события...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await bot.send_message(chat_id=message.chat.id,
                               text='События, которые вы ведёте',
                               reply_markup=ikb14(message.chat.id))
        await InitiatorState.show_my_list_events.set()
    else:
        await bot.send_message(chat_id=message.chat.id, text='Вы пока не ведёте ни одного события')
        await bot.send_message(chat_id=message.chat.id, text='Выберите пункт',
                               reply_markup=initiator_start_kb())
        await InitiatorState.wait_for.set()

# выбрал событие
async def choose_from_my_events(callback: types.CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split('_')[-1])
    bot = callback.bot
    await callback.message.delete()
    if event_id == 0:
        await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт',
                               reply_markup=initiator_start_kb())
        await InitiatorState.wait_for.set()
    else:
        text = get_text(event_id)
        await state.update_data(MYEV_ID=int(event_id)) # сохраняем данные
        await bot.send_message(chat_id=callback.from_user.id, text=text,
                               reply_markup=initiator_delete_kb())
        await InitiatorState.make_my_choose.set()

# вернуться к списку событий
async def return_to_my_event_cb(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await msg_initiator_events(callback.message, state)

# удалить событие
async def delete_my_event_cb(callback: types.CallbackQuery, state: FSMContext):
    event_id = await state.get_data('MYEV_ID') # получаем данные
    bot = callback.bot
    await callback.message.delete()
    logging.info('peck1')
    if delete_initiator_event(callback.from_user.id, event_id['MYEV_ID']):
        logging.info('peck2')
        await bot.send_message(chat_id=callback.from_user.id, text='Вы удалили событие')
        await state.reset_data()
        await InitiatorState.in_game.set()
        await msg_initiator_events(callback.message, state)
    else:
        await bot.send_message(chat_id=callback.from_user.id, text='Событие не было удалено, '
                                           'обратитесь к разработикам - @M1sterJack')
        await state.reset_data()
        await InitiatorState.in_game.set()
        await msg_initiator_events(callback.message, state)
        logging.info('Не удалось удалить участника')


# Добавить ивент
# выбор категории
# @dp.callback_query_handler(IsPrivateCb(), text='add_event', state='*')
async def msg_choose_category(message: types.Message, state: FSMContext):
    if categories_list():
        await message.answer(text='Готовим вопросы...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await message.answer(text='Выберите категорию',
                             reply_markup=ikb16())
        await InitiatorState.set_category.set()

async def msg_set_title(callback: types.CallbackQuery, state: FSMContext):
    category_id = callback.data.split('_')[-1]
    await callback.message.delete()
    await state.update_data(CATEGORY=str(category_id))
    bot = callback.bot
    await bot.send_message(chat_id=callback.from_user.id, text='Напишите название события')
    await InitiatorState.set_title.set()


# @dp.message_handler(IsPrivateMsg(), state=InitiatorState.set_title, content_types=types.ContentTypes.TEXT)
async def msg_set_about(message: types.Message, state: FSMContext):
    await state.update_data(TITLE=message.text.strip())
    await message.answer('Введите описание события (до 500 символов)')
    await InitiatorState.set_about.set()


# @dp.message_handler(IsPrivateMsg(), state=InitiatorState.set_about, content_types=types.ContentTypes.TEXT)
async def msg_set_date(message: types.Message, state: FSMContext):
    await state.update_data(ABOUT=message.text)
    await message.answer('Введите дату события в формате\n'
                         'Число-Месяц')
    await InitiatorState.set_date.set()


# @dp.message_handler(IsPrivateMsg(), state=InitiatorState.set_date, content_types=types.ContentTypes.TEXT)
async def msg_set_time(message: types.Message, state: FSMContext):
    if check_date(message.text) == None:
        await message.reply('Пожалуйста, введите дату события в формате\n'
                            'Число-Месяц')
        return
    else:
        date = check_date(message.text) + '-2023'
    await state.update_data(DATE=date)
    await message.answer('Введите время события (часовой пояс +3 - Московское время) в формате\n'
                         'Часы:Минуты')
    await InitiatorState.set_time.set()


# @dp.message_handler(IsPrivateMsg(), state=InitiatorState.set_time, content_types=types.ContentTypes.TEXT)
async def msg_set_number(message: types.Message, state: FSMContext):
    if check_time(message.text) == None:
        await message.reply('Пожалуйста, введите время события (часовой пояс '
                            '+3 - Московское время) в формате\n'
                            'Часы:Минуты')
        return
    await state.update_data(TIME=check_time(message.text))
    await message.answer('Введите число участников события')
    await InitiatorState.set_number.set()


# @dp.message_handler(IsPrivateMsg(), state=InitiatorState.set_number, content_types=types.ContentTypes.TEXT)
async def msg_set_confirm(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.reply("Пожалуйста, введите число участников события")
        return
    await state.update_data(NUMBER=message.text)
    context_data = await state.get_data()
    category = context_data.get('CATEGORY')
    title = context_data.get('TITLE')
    about = context_data.get('ABOUT')
    date = context_data.get('DATE')
    time = context_data.get('TIME')
    number = context_data.get('NUMBER')
    await message.answer(f"Подтвердите событие или вернитесь в начало, "
                         f"чтобы перезаполнить данные:\n"
                         f"Категория {category}\n{title}\n{about}\n{date} в {time}\n{number}",
                         reply_markup=confirm_ikb())
    await InitiatorState.confirm.set()

# вернулись в начало
async def cb_return_to_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.reset_data()
    await msg_choose_category(callback.message, state)

# последняя стадия добавления события - подтверждение события
# @dp.callback_query_handler(IsPrivateCb(), text='add_confirm', state=InitiatorState.confirm)
async def cb_add_confirm(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    context_data = await state.get_data()
    event_id, dt = save_event(callback.from_user.id,
                          context_data['CATEGORY'],
                          context_data['TITLE'],
                          context_data['ABOUT'],
                          context_data['DATE'],
                          context_data['TIME'],
                          context_data['NUMBER'])
    if event_id != False:
        await state.finish()
        await msg_send_all(callback, event_id)
        our_date = dt - datetime.timedelta(minutes=1)
        dtt = str(dt.strftime('%Y-%m-%d %H:%M:%S'))
        scheduler.add_job(func=send_reminder, trigger='date', run_date=our_date,
                          kwargs={'event_id': int(event_id), 'ini_id': int(callback.from_user.id),
                                  'title': str(context_data['TITLE']),
                                  'date': dtt},
                          timezone='Europe/Moscow')
        await callback.message.answer(text='Событие добавлено!',
                                      reply_markup=initiator_start_kb())
        await msg_main_menu(callback.message, state)
    else:
        await callback.message.answer(text='Событие не было опубликовано, повторите ввод или '
                                      'обратитесь к разработчикам - @M1sterJack',
                                      reply_markup=initiator_start_kb())
        await msg_main_menu(callback.message, state)

# главное меню для нового инициатора
async def custom_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.finish()
    await callback.message.answer('Выберите пункт', reply_markup=initiator_start_kb())
    await InitiatorState.wait_for.set()


# async def ini_get_url(callback: types.CallbackQuery, state: FSMContext):
#     await state.finish()
#     event_id = callback.data.split('_')[-1]
#     await callback.message.delete()
#     await callback.message.answer(text='Напишите в этот чат ссылку на событие')
#     await InitiatorState.wait_for_url.set()

def register_handlers_initiators(dp: Dispatcher):
    dp.register_message_handler(start_command, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                commands=['start'], state=None)
    dp.register_message_handler(msg_main_menu, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                commands=['main_menu'], state='*')
    dp.register_message_handler(ini_help, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                commands=['help'], state='*')

    dp.register_message_handler(msg_add_new_user, IsInitiatorMsgFilter(),
                                text='Подписаться на рассылку',
                                state='*')

    dp.register_message_handler(msg_delete_user, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                text='Отписаться от рассылки', state='*')

    dp.register_message_handler(my_list_events, IsInitiatorMsgFilter(),
                                text='Уже участвую', state='*')
    dp.register_callback_query_handler(choose_my_events, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       lambda callback: callback.data.startswith('even_'),
                                       state='*')
    dp.register_callback_query_handler(refuse_my_events, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='i_refuse_event',
                                       state=InitiatorState.make_choose)
    dp.register_callback_query_handler(return_cat, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='i_return_back', state=InitiatorState.make_choose)


    dp.register_message_handler(all_ini_category_list, IsInitiatorMsgFilter(), text='Могу поучаствовать',
                                state='*')
    dp.register_callback_query_handler(all_list_events, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       lambda callback: callback.data.startswith('cat_'),
                                       state='*')
    dp.register_callback_query_handler(cb_choose_events, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       lambda callback: callback.data.startswith('event_'),
                                       state=InitiatorState.show_events)
    dp.register_callback_query_handler(cb_agree, IsPrivateCb(), IsInitiatorMsgFilter(), text='ini_agree',
                                       state=InitiatorState.agree_disagree)
    dp.register_callback_query_handler(cb_disagree, IsPrivateCb(), IsInitiatorMsgFilter(), text='ini_disagree',
                                       state=InitiatorState.agree_disagree)

    # только для инициаторов
    dp.register_message_handler(msg_initiator_events, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                text='Мои ивенты', state='*')
    dp.register_callback_query_handler(choose_from_my_events, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       lambda callback: callback.data.startswith('myev_'),
                                       state=InitiatorState.show_my_list_events)
    dp.register_message_handler(msg_choose_category, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                text='Добавить ивент', state='*')
    dp.register_callback_query_handler(msg_set_title, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       lambda callback: callback.data.startswith('categ_'),
                                       state=InitiatorState.set_category)
    dp.register_callback_query_handler(return_to_my_event_cb, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='return_to_my_event', state=InitiatorState.make_my_choose)
    dp.register_callback_query_handler(delete_my_event_cb, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='delete_my_event', state=InitiatorState.make_my_choose)

    dp.register_message_handler(msg_set_about, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                state=InitiatorState.set_title,
                                content_types=types.ContentTypes.TEXT)
    dp.register_message_handler(msg_set_date, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                state=InitiatorState.set_about,
                                content_types=types.ContentTypes.TEXT)
    dp.register_message_handler(msg_set_time, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                state=InitiatorState.set_date,
                                content_types=types.ContentTypes.TEXT)
    dp.register_message_handler(msg_set_number, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                state=InitiatorState.set_time,
                                content_types=types.ContentTypes.TEXT)
    dp.register_message_handler(msg_set_confirm, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                state=InitiatorState.set_number,
                                content_types=types.ContentTypes.TEXT)
    dp.register_callback_query_handler(cb_add_confirm, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='add_confirm', state=InitiatorState.confirm)
    dp.register_callback_query_handler(cb_return_to_start, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='add_event', state=InitiatorState.confirm)
    # dp.register_callback_query_handler(ini_get_url, IsPrivateCb(), IsInitiatorMsgFilter(),
    #                                    lambda callback: callback.data.startswith('ini_url_'),
    #                                    state='*')
    dp.register_callback_query_handler(custom_main_menu, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='main_menu_custom', state='*')