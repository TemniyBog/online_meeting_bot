import asyncio
import logging

from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import ReplyKeyboardRemove

from connecting_bot.my_bot.db.db_commands import register_user, check_nickname, subscribe_user, delete_user, my_events, \
    get_text, refuse_user, get_categories_list, get_dict_events, check_count_of_participants, add_participant, \
    add_category
from connecting_bot.my_bot.filters.filters import IsPrivateCb, IsPrivateMsg
from connecting_bot.my_bot.handlers.initiators import initiator_welcome
from connecting_bot.my_bot.keyboards.admin_kb import kb3, \
    kb2, kb4, kb0, kb1, kb5
from connecting_bot.my_bot.states.admin_state import AdminState


# старт admins
async def admin_start_command(message: types.Message, state: FSMContext):
    register_user(message)
    await message.answer(text="Привет!\nВыберите пункт",
                         reply_markup=kb0())
    await AdminState.wait_for.set()

# command = main menu
async def admin_main_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Выберите пункт', reply_markup=kb0())
    await AdminState.wait_for.set()

# command = help
async def admin_help(message: types.Message, state: FSMContext):
    await message.answer('По всем интересующим Вас вопросам, а также в случае непредвиденных '
                         'ситуаций пишите в телеграм разрабочикам - @M1sterJack')

# Подписаться
# оформить подписку юзеру
# @dp.callback_query_handler(IsPrivateCb(), text='подписаться на рассылку', state=UserState.wait_for_choose)
async def admin_subscribe_user(message: types.Message, state: FSMContext):
    bot = message.bot
    subscribe_user(message.from_user.id)
    await message.answer(text="Вы подписаны на рассылку! Не включайте мьют, "
                              "здесь не будет рекламы)")
    await AdminState.in_game.set()

# Отписаться
# отписать юзера
# @dp.callback_query_handler(IsPrivateCb(), text='отписаться от рассылки', state=UserState.wait_for_choose)
async def admin_unsubscribe_user(message: types.Message, state: FSMContext):
    delete_user(message.from_user.id)
    await message.answer(text="Вы отписались от рассылки(")
    logging.info('admin')
    await AdminState.in_game.set()

# Уже участвую
# показываем события, в которых юзер участвует
async def admin_take_part_events(message: types.Message, state: FSMContext):
    events_id_title = my_events(message.chat.id)
    bot = message.bot
    # buttons_list = list()
    if events_id_title:
        await bot.send_message(chat_id=message.chat.id,
                               text='Ищем события...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await bot.send_message(chat_id=message.chat.id,
                               text='События, в которых вы участвуете',
                               reply_markup=kb3(message.chat.id))
        await AdminState.show_list_events.set()
    else:
        await bot.send_message(chat_id=message.chat.id,
                               text='Вы пока не участвуете ни в одном событии',
                               reply_markup=kb0())
        await AdminState.wait_for.set()

# выбрал событие
async def admin_choose_my_event(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split('_')[-1]
    logging.info('yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy')
    logging.info(f'{event_id}')
    bot = callback.bot
    await callback.message.delete()
    if int(event_id) == 0:
        await state.finish()
        await callback.message.answer('Выберите пункт', reply_markup=kb0())
        await AdminState.in_game.set()
    else:
        text = get_text(int(event_id))
        await state.update_data(ADMEV_ID=event_id) # сохраняем данные
        await bot.send_message(chat_id=callback.from_user.id, text=text,
                               reply_markup=kb1())
        await AdminState.make_choose.set()

# отказывается от участия
async def admin_refuse_participate(callback: types.CallbackQuery, state: FSMContext):
    event_id = await state.get_data('ADMEV_ID') # получаем данные
    logging.info(f'{event_id["ADMEV_ID"]}')
    await callback.message.delete()
    bot = callback.bot
    if refuse_user(callback.from_user.id, event_id['ADMEV_ID']):
        logging.info('check1')
        await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии')
        await admin_take_part_events(callback.message, state)
        await state.reset_data()
        await AdminState.in_game.set()
    else:
        await bot.send_message(chat_id=callback.from_user.id, text='Вы не были удалены из события, '
                                           'обратитесь к разработикам - @M1sterJack')
        await state.reset_data()
        await admin_take_part_events(callback.message, state)
        await AdminState.in_game.set()
        logging.info('Не удалось удалить участника')

# назад к списку категорий
async def admin_beetwen_my_list_events(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await admin_take_part_events(callback.message, state)
    await AdminState.show_categories.set()

# Могу поучаствовать
# показываем категории, если они есть
# будет работать только для приватных чатов
async def admin_all_category_list(message: types.Message, state: FSMContext):
    bot = message.bot
    if get_categories_list(message.chat.id):
        await bot.send_message(chat_id=message.chat.id, text='Ищем события...',
                               reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await bot.send_message(chat_id=message.chat.id, text='Выберите категорию',
                               reply_markup=kb2(message.from_user.id))
        await AdminState.show_categories.set()
    else:
        await bot.send_message(chat_id=message.chat.id, text='Пока нет событий',
                               reply_markup=kb0())
        await AdminState.wait_for.set()

# показываем ивенты по выбранной категории
async def admin_all_list_events(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split('_')[-1]
    await callback.message.delete()
    if category == '0':
        bot = callback.bot
        await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт',
                               reply_markup=kb0())
        await AdminState.wait_for.set()
    else:
        bot = callback.bot

        if get_dict_events(callback.from_user.id, category):
            await bot.send_message(chat_id=callback.from_user.id, text='Выберите событие',
                                   reply_markup=kb4(callback.from_user.id, category))
            await AdminState.show_events.set()
        else:
            await bot.send_message(chat_id=callback.from_user.id, text='Пока нет событий по этой категории')
            await admin_all_category_list(callback.message, state)
            await AdminState.show_categories.set()

# выбирает одно из событий
# @dp.callback_query_handler(IsPrivateCb(), lambda callback: callback.data.startswith('event_'),
#                            state=InitiatorState.events)
async def admin_choose_event(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split('_')[-1]
    await callback.message.delete()
    if int(event_id) == 0:
        await admin_all_category_list(callback.message, state)
        await AdminState.in_game.set()
    else:
        text = get_text(event_id)
        await state.update_data(event_id=event_id)
        bot = callback.bot
        await bot.send_message(chat_id=callback.from_user.id, text=text,
                               reply_markup=kb5())
        await AdminState.agree_disagree.set()


# участвует в событии
# @dp.callback_query_handler(IsPrivateCb(), text='agree', state=InitiatorState.agree_disagree)
async def admin_agree(callback: types.CallbackQuery, state: FSMContext):
    bot = callback.bot
    await callback.message.delete()
    async with state.proxy() as data:
        event_id = data['event_id']
    if check_count_of_participants(event_id):
        if add_participant(callback.from_user.id, event_id):
            await bot.send_message(chat_id=callback.from_user.id,
                                   text='Вам придёт ссылка-приглашение на событие, ожидайте')
            await state.reset_data()
            await AdminState.in_game.set()
            await admin_all_category_list(callback.message, state)
        else:
            await bot.send_message(chat_id=callback.from_user.id,
                                   text='Упс! Мы не смогли Вас добавить в участники события')
            await state.reset_data()
            await AdminState.in_game.set()
            await admin_all_category_list(callback.message, state)
    else:
        await state.reset_data()
        await bot.send_message(chat_id=callback.from_user.id,
                               text="К сожалению, на это мероприятие все места уже заняты, "
                                     "ожидайте объявление нового события")
        await state.reset_data()
        await AdminState.in_game.set()
        await admin_all_category_list(callback.message, state)


# отказывается участвовать
# @dp.callback_query_handler(IsPrivateCb(), text='disagree', state=InitiatorState.agree_disagree)
async def admin_disagree(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.finish()
    bot = callback.bot
    await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии!')
    await AdminState.in_game.set()
    await admin_all_category_list(callback.message, state)

    ########################################################################################
    # только для админов
# Добавить инициатора
# установить инициатора
# @dp.callback_query_handler(IsPrivateCb(), text='set_initiator')
async def admin_add_initiator(message: types.Message, state: FSMContext):
    await message.answer(text="Напиши никнейм инициатора "
                              "в формате @ник")
    await AdminState.wait_for_nick.set()

# @dp.message_handler(IsPrivateMsg())
async def admin_check_nickname(message: types.Message, state: FSMContext):
    user_id = check_nickname(message.text)
    if user_id is False:
        await message.answer(text="Пользователь не найден, повторите ввод "
                                  "или обратитесь к разработчикам - @M1sterJack",
                             reply_markup=kb0())
        await AdminState.in_game.set()
    else:
        await message.answer(text="Инициатор добавлен!",
                             reply_markup=kb0())
        await initiator_welcome(message, user_id)
        await AdminState.in_game.set()

# Добавить категорию
async def admin_add_category(message: types.Message, state: FSMContext):
    await message.answer(text="Напишите название категории")
    await AdminState.wait_for_category.set()

# получаем название категории
async def admin_take_name_category(message: types.Message, state: FSMContext):
    category = add_category(message.text)
    if category is False:
        await message.answer(text="Не удалось сохранить категорию в базе, "
                                  "попробуйте снова или обратитесь к разработчикам - @M1sterJack",
                             reply_markup=kb0())
        await AdminState.in_game.set()
    else:
        await message.answer(text="Категория добавлена!",
                             reply_markup=kb0())
        await AdminState.in_game.set()


def register_handlers_admins(dp : Dispatcher):
    dp.register_message_handler(admin_start_command, IsPrivateMsg(), is_admin=True,
                                commands=['start'], state=None)
    dp.register_message_handler(admin_main_menu, IsPrivateMsg(), is_admin=True,
                                commands=['main_menu'], state='*')
    dp.register_message_handler(admin_help, IsPrivateMsg(), is_admin=True,
                                commands=['help'], state='*')

    dp.register_message_handler(admin_subscribe_user, is_admin=True,
                                text='Подписаться на рассылку',
                                state='*')

    dp.register_message_handler(admin_unsubscribe_user, IsPrivateMsg(), is_admin=True,
                                text='Отписаться от рассылки', state='*')

    dp.register_message_handler(admin_take_part_events, IsPrivateMsg(), is_admin=True,
                                text='Уже участвую', state='*')
    dp.register_callback_query_handler(admin_choose_my_event,
                                       lambda callback: callback.data.startswith('admeven_'),
                                       IsPrivateCb(), is_admin=True,
                                       state='*')
    dp.register_callback_query_handler(admin_refuse_participate, IsPrivateCb(), is_admin=True,
                                       text='adm_refuse_event',
                                       state=AdminState.make_choose)
    dp.register_callback_query_handler(admin_beetwen_my_list_events, IsPrivateCb(), is_admin=True,
                                       text='adm_return_back', state=AdminState.make_choose)

    dp.register_message_handler(admin_all_category_list, is_admin=True, text='Могу поучаствовать',
                                state='*')
    dp.register_callback_query_handler(admin_all_list_events,
                                       lambda callback: callback.data.startswith('admcat_'),
                                       IsPrivateCb(), is_admin=True,
                                       state='*')
    dp.register_callback_query_handler(admin_choose_event,
                                       lambda callback: callback.data.startswith('event_'),
                                       IsPrivateCb(), is_admin=True,
                                       state=AdminState.show_events)
    dp.register_callback_query_handler(admin_agree, IsPrivateCb(), is_admin=True, text='adm_agree',
                                       state=AdminState.agree_disagree)
    dp.register_callback_query_handler(admin_disagree, IsPrivateCb(), is_admin=True, text='adm_disagree',
                                       state=AdminState.agree_disagree)


    dp.register_message_handler(admin_add_initiator, is_admin=True,
                                text = 'Добавить инициатора', state='*')
    dp.register_message_handler(admin_check_nickname, IsPrivateMsg(), content_types=types.ContentTypes.TEXT,
                                is_admin=True, state=AdminState.wait_for_nick)

    dp.register_message_handler(admin_add_category, is_admin=True,
                                text='Добавить категорию', state='*')
    dp.register_message_handler(admin_take_name_category, IsPrivateMsg(), content_types=types.ContentTypes.TEXT,
                                is_admin=True, state=AdminState.wait_for_category)