import asyncio

from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import ReplyKeyboardRemove
from loguru import logger

from connecting_bot.my_bot.bot_spec import bot
from connecting_bot.my_bot.db.db_commands import subscribe_user, delete_user, get_text, \
    get_categories_list, register_user, my_events, refuse_user, check_count_of_participants, add_participant, \
    get_user_dict_events, check_timezone, add_timezone, check_city
from connecting_bot.my_bot.filters.filters import IsPrivateMsg, IsPrivateCb
from connecting_bot.my_bot.keyboards.user_kb import kb20, kb21, kb22, kb23, kb24, kb25
from connecting_bot.my_bot.states.user_state import UserState


# старт
async def user_start_command(message: types.Message, state: FSMContext):
    try:
        register_user(message)
        await message.answer('Привет!\nВыберите пункт', reply_markup=kb20())
        await UserState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# главное меню
async def user_main_menu(message: types.Message, state: FSMContext):
    try:
        await state.finish()
        await message.answer('Выберите пункт', reply_markup=kb20())
        await UserState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# command = help
async def user_help(message: types.Message, state: FSMContext):
    try:
        await message.answer('По всем интересующим Вас вопросам, а также в случае непредвиденных '
                             'ситуаций пишите в телеграм разрабочикам - @slim1305')
    except Exception as err:
        logger.info(f'{err}')


# оформить подписку юзеру
async def user_subscribe_user(message: types.Message, state: FSMContext):
    try:
        if not check_timezone(message.from_user.id):
            await message.answer(text="Сначала Вы должны установить ваш часовой пояс.\n"
                                      "Это можно сделать через кнопку главного меню")
        else:
            subscribe_user(message.from_user.id)
            await message.answer(text="Вы подписаны на рассылку! Не включайте мьют, "
                                      "здесь не будет рекламы)")
            await UserState.in_game.set()
    except Exception as err:
        logger.info(f'{err}')


# отписать юзера
async def user_unsubscribe_user(message: types.Message, state: FSMContext):
    try:
        delete_user(message.from_user.id)
        await message.answer(text="Вы отписались от рассылки(")
        await UserState.in_game.set()
    except Exception as err:
        logger.info(f'{err}')


# Уже участвую
# показываем события, в которых юзер участвует
async def user_take_part_events(message: types.Message, state: FSMContext):
    try:
        events_id_title = my_events(message.chat.id)
        if events_id_title:
            await bot.send_message(chat_id=message.chat.id,
                                   text='Ищем события...', reply_markup=ReplyKeyboardRemove())
            await asyncio.sleep(1)
            await bot.send_message(chat_id=message.chat.id,
                                   text='События, в которых вы участвуете',
                                   reply_markup=kb23(events_id_title))
            await UserState.show_list_events.set()
        else:
            await bot.send_message(chat_id=message.chat.id,
                                   text='Вы пока не участвуете ни в одном событии',
                                   reply_markup=kb20())
            await UserState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# выбрал событие
async def user_choose_my_event(callback: types.CallbackQuery, state: FSMContext):
    try:
        event_id = int(callback.data.split('_')[-1])
        await callback.message.delete()
        if event_id == 0:
            await state.finish()
            await callback.message.answer('Выберите пункт', reply_markup=kb20())
            await UserState.in_game.set()
        else:
            text = get_text(event_id, callback.from_user.id)
            await state.update_data(EVEN_ID=event_id)  # сохраняем данные
            await bot.send_message(chat_id=callback.from_user.id, text=text,
                                   reply_markup=kb24())
            await UserState.make_choose.set()
    except Exception as err:
        logger.info(f'{err}')


# отказывается от участия
async def user_refuse_participate(callback: types.CallbackQuery, state: FSMContext):
    try:
        event_id = await state.get_data('EVEN_ID')  # получаем данные
        await callback.message.delete()
        if refuse_user(callback.from_user.id, event_id['EVEN_ID']):
            await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии')
            await user_take_part_events(callback.message, state)
            await state.reset_data()
            await UserState.in_game.set()
        else:
            await bot.send_message(chat_id=callback.from_user.id,
                                   text='Вы не были удалены из события, '
                                        'обратитесь к разработикам - @slim1305')
            await state.reset_data()
            await user_take_part_events(callback.message, state)
            await UserState.in_game.set()
            logger.info('Не удалось удалить участника')
    except Exception as err:
        logger.info(f'{err}')


# прокладка для коллбека
async def user_beetwen_my_list_events(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        await user_take_part_events(callback.message, state)
        await UserState.in_game.set()
    except Exception as err:
        logger.info(f'{err}')


# Могу поучаствовать
# показываем категории, если они есть
async def user_all_category_list(message: types.Message, state: FSMContext):
    try:
        categories_list = get_categories_list(message.chat.id)
        if categories_list:
            await message.answer(text='Ищем категории...', reply_markup=ReplyKeyboardRemove())
            await asyncio.sleep(1)
            await message.answer(text='Выберите категорию',
                                 reply_markup=kb22(categories_list))
            await UserState.show_categories.set()
        else:
            await bot.send_message(chat_id=message.chat.id, text='Пока нет событий',
                                   reply_markup=kb20())
            await UserState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# показываем ивенты по выбранной категории
async def user_all_list_events(callback: types.CallbackQuery, state: FSMContext):
    try:
        category = callback.data.split('_')[-1]
        await callback.message.delete()
        if category == '0':
            await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт',
                                   reply_markup=kb20())
            await UserState.wait_for.set()
        else:
            buttons_dict = get_user_dict_events(callback.from_user.id, category)
            if buttons_dict:

                await bot.send_message(chat_id=callback.from_user.id, text='Выберите событие',
                                       reply_markup=kb21(buttons_dict))
                await UserState.show_events.set()
            else:
                await bot.send_message(chat_id=callback.from_user.id, text='Пока нет событий по этой категории')
                await user_all_category_list(callback.message, state)
                await UserState.show_categories.set()
    except Exception as err:
        logger.info(f'{err}')


# выбирает одно из событий
async def user_choose_events(callback: types.CallbackQuery, state: FSMContext):
    try:
        event_id = int(callback.data.split('_')[-1])
        await callback.message.delete()
        if event_id == 0:
            await user_all_category_list(callback.message, state)
            await UserState.in_game.set()
        else:
            text = get_text(event_id, callback.from_user.id)
            await state.update_data(usevent_id=event_id)
            await bot.send_message(chat_id=callback.from_user.id, text=text,
                                   reply_markup=kb25())
            await UserState.agree_disagree.set()
    except Exception as err:
        logger.info(f'{err}')


# участвует в событии
async def user_agree(callback: types.CallbackQuery, state: FSMContext):
    try:
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
    except Exception as err:
        logger.info(f'{err}')


# отказывается участвовать
async def user_disagree(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        await state.finish()
        await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии!')
        await UserState.in_game.set()
        await user_all_category_list(callback.message, state)
    except Exception as err:
        logger.info(f'{err}')


# ответил на рассылку Принять участие или 0 = Отказаться
async def group_answer_to_mailing(callback: types.CallbackQuery, state: FSMContext):
    try:
        event_id = int(callback.data.split('_')[-1])
        await callback.message.delete()
        if event_id == 0:
            pass
        else:
            if check_count_of_participants(event_id):
                if add_participant(callback.from_user.id, event_id):
                    await bot.send_message(chat_id=callback.from_user.id,
                                           text='Вам придёт ссылка-приглашение на событие, ожидайте')
                else:
                    await bot.send_message(chat_id=callback.from_user.id,
                                           text='Упс! Мы не смогли Вас добавить в участники события')
            else:
                await bot.send_message(chat_id=callback.from_user.id,
                                       text="К сожалению, на это мероприятие все места уже заняты, "
                                            "ожидайте объявление нового события.")
    except Exception as err:
        logger.info(f'{err}')


# Установить часовой пояс
async def user_check_city(message: types.Message, state: FSMContext):
    try:
        timezone = check_timezone(message.from_user.id)
        if timezone:
            await bot.send_message(message.from_user.id, f'Сейчас у вас установлен часовой пояс - {timezone}\n'
                                                         f'Если вы хотите его поменять - просто введите '
                                                         f'название своего города.\n'
                                                         f'Если вы не хотите его менять - нажмите '
                                                         f'"Главное меню" в меню сбоку',
                                   reply_markup=ReplyKeyboardRemove())
            await UserState.wait_for_city.set()
        else:
            await bot.send_message(message.from_user.id, 'Пожалуйста, напишите название вашего города.\n'
                                                         'Мы используем это для установления часового пояса.',
                                   reply_markup=ReplyKeyboardRemove())
            await UserState.wait_for_city.set()
    except Exception as err:
        logger.info(f'{err}')


# проверяем то, что ввёл юзер, и пытаемся установить часовой пояс
async def user_add_timezone(message: types.Message, state: FSMContext):
    try:
        timezone_str, timezone_hours = check_city(message.text)
        if timezone_str == None:
            await message.answer("Не удалось найти такой город. "
                                 "Попробуйте написать его название латиницей "
                                 "или указать более крупный город поблизости.")
            return
        else:
            add_timezone(message.from_user.id, timezone_str)
            await state.finish()
            await message.answer(f"Часовой пояс установлен в {timezone_str} ({timezone_hours} от GMT)\n"
                                 f"Вы всегда можете изменить его через кнопку главного меню",
                                 reply_markup=kb20())
            await UserState.in_game.set()
    except Exception as err:
        logger.info(f'{err}')


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

    dp.register_message_handler(user_check_city, IsPrivateMsg(),
                                text='Установить часовой пояс', state='*')
    dp.register_message_handler(user_add_timezone, IsPrivateMsg(),
                                state=UserState.wait_for_city,
                                content_types=types.ContentTypes.TEXT)
