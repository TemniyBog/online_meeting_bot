import asyncio
import logging

from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import ReplyKeyboardRemove

from connecting_bot.my_bot.bot_spec import bot
from connecting_bot.my_bot.db.db_commands import subscribe_user, delete_user, get_text, \
    get_categories_list, register_user, my_events, refuse_user, check_count_of_participants, add_participant, \
    get_user_dict_events
from connecting_bot.my_bot.filters.filters import IsPrivateMsg, IsPrivateCb
from connecting_bot.my_bot.keyboards.user_kb import kb20, kb21, kb22, kb23, kb24, kb25
from connecting_bot.my_bot.states.user_state import UserState


# старт
async def user_start_command(message: types.Message, state: FSMContext):
    register_user(message)
    await message.answer('Привет!\nВыберите пункт', reply_markup=kb20())
    await UserState.wait_for.set()

# главное меню
async def user_main_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Выберите пункт', reply_markup=kb20())
    await UserState.wait_for.set()

# command = help
async def user_help(message: types.Message, state: FSMContext):
    await message.answer('По всем интересующим Вас вопросам, а также в случае непредвиденных '
                         'ситуаций пишите в телеграм разрабочикам - @M1sterJack')

# оформить подписку юзеру
async def user_subscribe_user(message: types.Message, state: FSMContext):
    subscribe_user(message.from_user.id)
    await message.answer(text="Вы подписаны на рассылку! Не включайте мьют, "
                         "здесь не будет рекламы)")
    await UserState.in_game.set()

# отписать юзера
async def user_unsubscribe_user(message: types.Message, state: FSMContext):
    delete_user(message.from_user.id)
    await message.answer(text="Вы отписались от рассылки(")
    logging.info('user')
    await UserState.in_game.set()

# Уже участвую
# показываем события, в которых юзер участвует
async def user_take_part_events(message: types.Message, state: FSMContext):
    if my_events(message.chat.id):
        await bot.send_message(chat_id=message.chat.id,
                               text='Ищем события...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await bot.send_message(chat_id=message.chat.id,
                               text='События, в которых вы участвуете',
                               reply_markup=kb23(message.chat.id))
        await UserState.show_list_events.set()
    else:
        await bot.send_message(chat_id=message.chat.id,
                               text='Вы пока не участвуете ни в одном событии',
                               reply_markup=kb20())
        await UserState.wait_for.set()

# выбрал событие
async def user_choose_my_event(callback: types.CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split('_')[-1])
    logging.info('yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy')
    logging.info(f'{event_id}')
    bot = callback.bot
    await callback.message.delete()
    if event_id == 0:
        await state.finish()
        await callback.message.answer('Выберите пункт', reply_markup=kb20())
        await UserState.in_game.set()
    else:
        text = get_text(event_id)
        await state.update_data(EVEN_ID=event_id) # сохраняем данные
        await bot.send_message(chat_id=callback.from_user.id, text=text,
                               reply_markup=kb24())
        await UserState.make_choose.set()

# отказывается от участия
async def user_refuse_participate(callback: types.CallbackQuery, state: FSMContext):
    event_id = await state.get_data('EVEN_ID') # получаем данные
    logging.info(f'{event_id["EVEN_ID"]}')
    bot = callback.bot
    await callback.message.delete()
    if refuse_user(callback.from_user.id, event_id['EVEN_ID']):
        logging.info('check1')
        await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии')
        await user_take_part_events(callback.message, state)
        await state.reset_data()
        await UserState.in_game.set()
    else:
        await bot.send_message(chat_id=callback.from_user.id,
                               text='Вы не были удалены из события, '
                                    'обратитесь к разработикам - @M1sterJack')
        await state.reset_data()
        await user_take_part_events(callback.message, state)
        await UserState.in_game.set()
        logging.info('Не удалось удалить участника')

# прокладка для коллбека
async def user_beetwen_my_list_events(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await user_take_part_events(callback.message, state)
    await UserState.in_game.set()

# Могу поучаствовать
# показываем категории, если они есть
async def user_all_category_list(message: types.Message, state: FSMContext):
    if get_categories_list(message.chat.id):
        await message.answer(text='Ищем события...', reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await message.answer(text='Выберите категорию',
                             reply_markup=kb22(message.from_user.id))
        await UserState.show_categories.set()
    else:
        await bot.send_message(chat_id=message.chat.id, text='Пока нет событий',
                               reply_markup=kb20())
        await UserState.wait_for.set()

# показываем ивенты по выбранной категории
async def user_all_list_events(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split('_')[-1]
    await callback.message.delete()
    logging.info(f'{await state.get_state()}')
    if category == '0':
        bot = callback.bot
        await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт',
                               reply_markup=kb20())
        await UserState.wait_for.set()
    else:
        bot = callback.bot
        if get_user_dict_events(callback.from_user.id, category):
            await bot.send_message(chat_id=callback.from_user.id, text='Выберите событие',
                                   reply_markup=kb21(callback.from_user.id, category))
            await UserState.show_events.set()
        else:
            await bot.send_message(chat_id=callback.from_user.id, text='Пока нет событий по этой категории')
            await user_all_category_list(callback.message, state)
            await UserState.show_categories.set()

# выбирает одно из событий
async def user_choose_events(callback: types.CallbackQuery, state: FSMContext):
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
                               reply_markup=kb25())
        await UserState.agree_disagree.set()

# участвует в событии
async def user_agree(callback: types.CallbackQuery, state: FSMContext):
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

# отказывается участвовать
async def user_disagree(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.finish()
    bot = callback.bot
    await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии!')
    await UserState.in_game.set()
    await user_all_category_list(callback.message, state)

# ответил на рассылку Принять участие или 0 = Отказаться
async def group_answer_to_mailing(callback: types.CallbackQuery, state: FSMContext):
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
    dp.register_message_handler(user_start_command, IsPrivateMsg(), commands=['start'], state=None)
    dp.register_message_handler(user_main_menu, IsPrivateMsg(), commands=['main_menu'], state='*')
    dp.register_message_handler(user_help, IsPrivateMsg(), commands=['help'], state='*')

    dp.register_message_handler(user_subscribe_user,
                                text='Подписаться на рассылку', state='*')
    dp.register_message_handler(user_unsubscribe_user, IsPrivateMsg(),
                                text='Отписаться от рассылки', state='*')
    #
    dp.register_message_handler(user_take_part_events, text='Уже участвую', state='*')
    dp.register_callback_query_handler(user_choose_my_event, IsPrivateCb(),
                                       lambda callback: callback.data.startswith('ev_'),
                                       state='*')
    dp.register_callback_query_handler(user_refuse_participate, IsPrivateCb(),
                                       text='refuse_event',
                                       state=UserState.make_choose)
    dp.register_callback_query_handler(user_beetwen_my_list_events, IsPrivateCb(),
                                       text='return_back',
                                       state=UserState.make_choose)

    dp.register_message_handler(user_all_category_list, text='Могу поучаствовать', state='*')
    dp.register_callback_query_handler(user_all_list_events, IsPrivateCb(),
                                       lambda callback: callback.data.startswith('category_'),
                                       state='*')
    dp.register_callback_query_handler(user_choose_events, IsPrivateCb(),
                                       lambda callback: callback.data.startswith('usevent_'),
                                       state=UserState.show_events)
    dp.register_callback_query_handler(user_agree, IsPrivateCb(), text='agree',
                                       state=UserState.agree_disagree)
    dp.register_callback_query_handler(user_disagree, IsPrivateCb(), text='disagree',
                                       state=UserState.agree_disagree)
    dp.register_callback_query_handler(group_answer_to_mailing, IsPrivateCb(),
                                       lambda callback: callback.data.startswith('sign_up_'),
                                       state='*')
