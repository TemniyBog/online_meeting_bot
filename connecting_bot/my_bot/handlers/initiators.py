import asyncio
import datetime
import logging

from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import ReplyKeyboardRemove

from connecting_bot.my_bot.bot_spec import scheduler, bot
from connecting_bot.my_bot.db.db_commands import save_event, \
    check_time, check_date, get_text, add_participant, check_count_of_participants, \
    get_dict_events, register_user, subscribe_user, delete_user, my_events, refuse_user, \
    get_categories_list, show_ini_events, delete_initiator_event, categories_list
from connecting_bot.my_bot.filters.filters import IsPrivateCb, IsPrivateMsg, IsInitiatorMsgFilter
from connecting_bot.my_bot.keyboards.initiator_kb import kb10, kb11, kb12, kb13, kb14, kb15, kb16, kb17, kb18, kb19, \
    kb00
from connecting_bot.my_bot.misc.functions import msg_send_all, send_reminder
from connecting_bot.my_bot.states.initiator_state import InitiatorState


# старт инициаторы
async def initiator_start_command(message: types.Message, state: FSMContext):
    register_user(message)
    await message.answer(text="Привет!\nВыберите пункт",
                         reply_markup=kb10())
    await InitiatorState.wait_for.set()

# command = main menu
async def initiator_main_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Выберите пункт', reply_markup=kb10())
    await InitiatorState.wait_for.set()

# command = help
async def initiator_help(message: types.Message, state: FSMContext):
    await message.answer('По всем интересующим Вас вопросам, а также в случае непредвиденных '
                         'ситуаций пишите в телеграм разрабочикам - @M1sterJack')

# приглашение нового инициатора
# функция без хэндлера
async def initiator_welcome(message: types.Message, user_id):
    bot = message.bot
    await bot.send_message(chat_id=user_id,
                           text='Вы назначены инициатором, '
                                'зайдите в Главное меню',
                           reply_markup=kb00())

# главное меню для нового инициатора
async def initiator_custom_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.finish()
    await callback.message.answer('Выберите пункт', reply_markup=kb10())
    await InitiatorState.wait_for.set()




# Подписаться
# оформить подписку юзеру
async def initiator_subscribe_user(message: types.Message, state: FSMContext):
    subscribe_user(message.from_user.id)
    await message.answer(text="Вы подписаны на рассылку! Не включайте мьют, "
                              "здесь не будет рекламы)")
    await InitiatorState.in_game.set()

# Отписаться
# отписать юзера
async def initiator_unsubscribe_user(message: types.Message, state: FSMContext):
    delete_user(message.from_user.id)
    await message.answer(text="Вы отписались от рассылки(")
    logging.info('initiator')
    await InitiatorState.in_game.set()

# Уже участвую
# показываем события, в которых юзер участвует
async def initiator_take_part_events(message: types.Message, state: FSMContext):
    if my_events(message.chat.id):
        await bot.send_message(chat_id=message.chat.id,
                               text='Ищем события...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await bot.send_message(chat_id=message.chat.id,
                               text='События, в которых вы участвуете',
                               reply_markup=kb13(message.chat.id))
        await InitiatorState.show_list_events.set()
    else:
        await bot.send_message(chat_id=message.chat.id,
                               text='Вы пока не участвуете ни в одном событии',
                               reply_markup=kb10())
        await InitiatorState.wait_for.set()

# выбрал событие
async def initiator_choose_my_event(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split('_')[-1]
    await callback.message.delete()
    if int(event_id) == 0:
        await state.finish()
        await callback.message.answer('Выберите пункт', reply_markup=kb10())
        await InitiatorState.in_game.set()
    else:
        text = get_text(int(event_id))
        await state.update_data(EV_ID=event_id) # сохраняем данные
        await bot.send_message(chat_id=callback.from_user.id, text=text,
                               reply_markup=kb18())
        await InitiatorState.make_choose.set()

# отказывается от участия
async def initiator_refuse_participate(callback: types.CallbackQuery, state: FSMContext):
    event_id = await state.get_data('EV_ID') # получаем данные
    logging.info(f'{event_id["EV_ID"]}')
    bot = callback.bot
    await callback.message.delete()
    if refuse_user(callback.from_user.id, event_id['EV_ID']):
        logging.info('check1')
        await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии')
        await initiator_take_part_events(callback.message, state)
        await state.reset_data()
        await InitiatorState.in_game.set()
    else:
        await bot.send_message(chat_id=callback.from_user.id, text='Вы не были удалены из события, '
                                           'обратитесь к разработикам - @M1sterJack')
        await state.reset_data()
        await initiator_take_part_events(callback.message, state)
        await InitiatorState.in_game.set()
        logging.info('Не удалось удалить участника')

# назад к списку категорий
async def initiator_beetwen_my_list_events(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await initiator_take_part_events(callback.message, state)
    await InitiatorState.show_categories.set()

# Могу поучаствовать
# показываем категории, если они есть
async def initiator_all_category_list(message: types.Message, state: FSMContext):
    if get_categories_list(message.chat.id):
        await message.answer(text='Ищем события...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await message.answer(text='Выберите категорию',
                             reply_markup=kb12(message.chat.id))
        await InitiatorState.show_categories.set()
    else:
        await bot.send_message(chat_id=message.chat.id, text='Пока нет событий',
                               reply_markup=kb10())
        await InitiatorState.wait_for.set()

# показываем ивенты по выбранной категории
async def initiator_all_list_events(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split('_')[-1]
    await callback.message.delete()
    logging.info(f'{await state.get_state()}')
    if category == '0':
        bot = callback.bot
        await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт',
                               reply_markup=kb10())
        await InitiatorState.wait_for.set()
    else:
        bot = callback.bot
        if get_dict_events(callback.from_user.id, category):
            await bot.send_message(chat_id=callback.from_user.id, text='Выберите событие',
                                   reply_markup=kb11(callback.from_user.id, category))
            await InitiatorState.show_events.set()
        else:
            await bot.send_message(chat_id=callback.from_user.id, text='Пока нет событий по этой категории')
            await initiator_all_category_list(callback.message, state)
            await InitiatorState.show_categories.set()

# выбирает одно из событий
async def initiator_choose_events(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split('_')[-1]
    await callback.message.delete()
    if int(event_id) == 0:
        await initiator_all_category_list(callback.message, state)
        await InitiatorState.in_game.set()
    else:
        text = get_text(event_id)
        await state.update_data(event_id=event_id)
        bot = callback.bot
        await bot.send_message(chat_id=callback.from_user.id, text=text,
                               reply_markup=kb19())
        await InitiatorState.agree_disagree.set()

# участвует в событии
async def initiator_agree(callback: types.CallbackQuery, state: FSMContext):
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
            await initiator_all_category_list(callback.message, state)
        else:
            await bot.send_message(chat_id=callback.from_user.id,
                                   text='Упс! Мы не смогли Вас добавить в участники события')
            await state.reset_data()
            await InitiatorState.in_game.set()
            await initiator_all_category_list(callback.message, state)
    else:
        await state.reset_data()
        await bot.send_message(chat_id=callback.from_user.id,
                               text="К сожалению, на это мероприятие все места уже заняты, "
                                     "ожидайте объявление нового события")
        await state.reset_data()
        await InitiatorState.in_game.set()
        await initiator_all_category_list(callback.message, state)


# отказывается участвовать
async def initiator_disagree(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.finish()
    bot = callback.bot
    await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии!')
    await InitiatorState.in_game.set()
    await initiator_all_category_list(callback.message, state)


# только для инициаторов #################################
# Мои ивенты
# ивенты инициатора, которые он инициировал
async def initiator_my_events(message: types.Message, state: FSMContext):
    if show_ini_events(message.chat.id):
        await bot.send_message(chat_id=message.chat.id,
                               text='Ищем события...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await bot.send_message(chat_id=message.chat.id,
                               text='События, которые вы ведёте',
                               reply_markup=kb14(message.chat.id))
        await InitiatorState.show_my_list_events.set()
    else:
        await bot.send_message(chat_id=message.chat.id, text='Вы пока не ведёте ни одного события',
                               reply_markup=kb10())
        await InitiatorState.wait_for.set()

# выбрал событие
async def initiator_choose_from_my_event(callback: types.CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split('_')[-1])
    bot = callback.bot
    await callback.message.delete()
    if event_id == 0:
        await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт',
                               reply_markup=kb10())
        await InitiatorState.wait_for.set()
    else:
        text = get_text(event_id)
        await state.update_data(MYEV_ID=int(event_id)) # сохраняем данные
        await bot.send_message(chat_id=callback.from_user.id, text=text,
                               reply_markup=kb17())
        await InitiatorState.make_my_choose.set()

# вернуться к списку событий
async def initiator_return_my_events(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await initiator_my_events(callback.message, state)

# удалить событие
async def initiator_delete_my_event(callback: types.CallbackQuery, state: FSMContext):
    event_id = await state.get_data('MYEV_ID') # получаем данные
    bot = callback.bot
    await callback.message.delete()
    logging.info('peck1')
    if delete_initiator_event(callback.from_user.id, event_id['MYEV_ID']):
        logging.info('peck2')
        await bot.send_message(chat_id=callback.from_user.id, text='Вы удалили событие')
        await state.reset_data()
        await InitiatorState.in_game.set()
        await initiator_my_events(callback.message, state)
    else:
        await bot.send_message(chat_id=callback.from_user.id, text='Событие не было удалено, '
                                           'обратитесь к разработикам - @M1sterJack')
        await state.reset_data()
        await InitiatorState.in_game.set()
        await initiator_my_events(callback.message, state)
        logging.info('Не удалось удалить участника')


# Добавить ивент
# вводим данные по событию
async def initiator_set_category(message: types.Message, state: FSMContext):
    if categories_list():
        await message.answer(text='Готовим вопросы...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await message.answer(text='Выберите категорию',
                             reply_markup=kb16())
        await InitiatorState.set_category.set()

async def initiator_set_title(callback: types.CallbackQuery, state: FSMContext):
    category_id = callback.data.split('_')[-1]
    await callback.message.delete()
    await state.update_data(CATEGORY=str(category_id))
    bot = callback.bot
    await bot.send_message(chat_id=callback.from_user.id, text='Напишите название события')
    await InitiatorState.set_title.set()


async def initiator_set_about(message: types.Message, state: FSMContext):
    await state.update_data(TITLE=message.text.strip())
    await message.answer('Введите описание события (до 500 символов)')
    await InitiatorState.set_about.set()


async def initiator_set_date(message: types.Message, state: FSMContext):
    await state.update_data(ABOUT=message.text)
    await message.answer('Введите дату события в формате\n'
                         'Число-Месяц')
    await InitiatorState.set_date.set()


async def initiator_set_time(message: types.Message, state: FSMContext):
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


async def initiator_set_number_participants(message: types.Message, state: FSMContext):
    if check_time(message.text) == None:
        await message.reply('Пожалуйста, введите время события (часовой пояс '
                            '+3 - Московское время) в формате\n'
                            'Часы:Минуты')
        return
    await state.update_data(TIME=check_time(message.text))
    await message.answer('Введите число участников события')
    await InitiatorState.set_number.set()


async def initiator_set_confirm(message: types.Message, state: FSMContext):
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
                         reply_markup=kb15())
    await InitiatorState.confirm.set()

# последняя стадия добавления события - подтверждение события
async def initiator_add_event(callback: types.CallbackQuery, state: FSMContext):
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
                                      reply_markup=kb10())
        await initiator_main_menu(callback.message, state)
    else:
        await callback.message.answer(text='Событие не было опубликовано, повторите ввод или '
                                      'обратитесь к разработчикам - @M1sterJack',
                                      reply_markup=kb10())
        await initiator_main_menu(callback.message, state)

# вернулись в начало
async def initiator_return_to_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.reset_data()
    await initiator_set_category(callback.message, state)

def register_handlers_initiators(dp: Dispatcher):
    dp.register_message_handler(initiator_start_command, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                commands=['start'], state=None)
    dp.register_message_handler(initiator_main_menu, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                commands=['main_menu'], state='*')
    dp.register_message_handler(initiator_help, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                commands=['help'], state='*')

    dp.register_callback_query_handler(initiator_custom_main_menu, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='main_menu_custom', state='*')

    dp.register_message_handler(initiator_subscribe_user, IsInitiatorMsgFilter(),
                                text='Подписаться на рассылку',
                                state='*')
    dp.register_message_handler(initiator_unsubscribe_user, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                text='Отписаться от рассылки', state='*')

    dp.register_message_handler(initiator_take_part_events, IsInitiatorMsgFilter(),
                                text='Уже участвую', state='*')
    dp.register_callback_query_handler(initiator_choose_my_event, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       lambda callback: callback.data.startswith('even_'),
                                       state='*')
    dp.register_callback_query_handler(initiator_refuse_participate, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='i_refuse_event',
                                       state=InitiatorState.make_choose)
    dp.register_callback_query_handler(initiator_beetwen_my_list_events, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='i_return_back', state=InitiatorState.make_choose)

    dp.register_message_handler(initiator_all_category_list, IsInitiatorMsgFilter(), text='Могу поучаствовать',
                                state='*')
    dp.register_callback_query_handler(initiator_all_list_events, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       lambda callback: callback.data.startswith('cat_'),
                                       state='*')
    dp.register_callback_query_handler(initiator_choose_events, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       lambda callback: callback.data.startswith('event_'),
                                       state=InitiatorState.show_events)
    dp.register_callback_query_handler(initiator_agree, IsPrivateCb(), IsInitiatorMsgFilter(), text='ini_agree',
                                       state=InitiatorState.agree_disagree)
    dp.register_callback_query_handler(initiator_disagree, IsPrivateCb(), IsInitiatorMsgFilter(), text='ini_disagree',
                                       state=InitiatorState.agree_disagree)

    # только для инициаторов
    dp.register_message_handler(initiator_my_events, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                text='Мои ивенты', state='*')
    dp.register_callback_query_handler(initiator_choose_from_my_event, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       lambda callback: callback.data.startswith('myev_'),
                                       state=InitiatorState.show_my_list_events)
    dp.register_callback_query_handler(initiator_return_my_events, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='return_to_my_event', state=InitiatorState.make_my_choose)
    dp.register_callback_query_handler(initiator_delete_my_event, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='delete_my_event', state=InitiatorState.make_my_choose)

    dp.register_message_handler(initiator_set_category, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                text='Добавить ивент', state='*')
    dp.register_callback_query_handler(initiator_set_title, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       lambda callback: callback.data.startswith('categ_'),
                                       state=InitiatorState.set_category)
    dp.register_message_handler(initiator_set_about, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                state=InitiatorState.set_title,
                                content_types=types.ContentTypes.TEXT)
    dp.register_message_handler(initiator_set_date, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                state=InitiatorState.set_about,
                                content_types=types.ContentTypes.TEXT)
    dp.register_message_handler(initiator_set_time, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                state=InitiatorState.set_date,
                                content_types=types.ContentTypes.TEXT)
    dp.register_message_handler(initiator_set_number_participants, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                state=InitiatorState.set_time,
                                content_types=types.ContentTypes.TEXT)
    dp.register_message_handler(initiator_set_confirm, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                state=InitiatorState.set_number,
                                content_types=types.ContentTypes.TEXT)
    dp.register_callback_query_handler(initiator_add_event, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='add_confirm', state=InitiatorState.confirm)
    dp.register_callback_query_handler(initiator_return_to_start, IsPrivateCb(), IsInitiatorMsgFilter(),
                                       text='add_event', state=InitiatorState.confirm)
