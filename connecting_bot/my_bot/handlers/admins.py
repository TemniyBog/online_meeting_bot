import asyncio

from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import ReplyKeyboardRemove
from loguru import logger

from connecting_bot.my_bot.bot_spec import bot
from connecting_bot.my_bot.db.db_commands import register_user, check_nickname, subscribe_user, delete_user, my_events, \
    get_text, refuse_user, get_categories_list, check_count_of_participants, add_participant, \
    add_category, check_timezone, check_city, add_timezone, get_admin_dict_events
from connecting_bot.my_bot.filters.filters import IsPrivateCb, IsPrivateMsg
from connecting_bot.my_bot.handlers.initiators import initiator_welcome
from connecting_bot.my_bot.keyboards.admin_kb import kb3, \
    kb2, kb4, kb0, kb1, kb5
from connecting_bot.my_bot.states.admin_state import AdminState


# старт admins
async def admin_start_command(message: types.Message, state: FSMContext):
    try:
        register_user(message)
        await message.answer(text="Привет!\nВыберите пункт",
                             reply_markup=kb0())
        await AdminState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# command = main menu
async def admin_main_menu(message: types.Message, state: FSMContext):
    try:
        await state.finish()
        await message.answer('Выберите пункт', reply_markup=kb0())
        await AdminState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# command = help
async def admin_help(message: types.Message, state: FSMContext):
    try:
        await message.answer('По всем интересующим Вас вопросам, а также в случае непредвиденных '
                             'ситуаций пишите в телеграм разрабочикам - @slim1305')
    except Exception as err:
        logger.info(f'{err}')


# Подписаться
# оформить подписку юзеру
async def admin_subscribe_user(message: types.Message, state: FSMContext):
    try:
        if not check_timezone(message.from_user.id):
            await message.answer(text="Сначала Вы должны установить ваш часовой пояс.\n"
                                      "Это можно сделать через кнопку главного меню")
        else:
            subscribe_user(message.from_user.id)
            await message.answer(text="Вы подписаны на рассылку! Не включайте мьют, "
                                      "здесь не будет рекламы)")
            await AdminState.in_game.set()
    except Exception as err:
        logger.info(f'{err}')


# Отписаться
# отписать юзера
async def admin_unsubscribe_user(message: types.Message, state: FSMContext):
    try:
        delete_user(message.from_user.id)
        await message.answer(text="Вы отписались от рассылки(")
        await AdminState.in_game.set()
    except Exception as err:
        logger.info(f'{err}')


# Уже участвую
# показываем события, в которых юзер участвует
async def admin_take_part_events(message: types.Message, state: FSMContext):
    try:
        events_id_title = my_events(message.chat.id)
        if events_id_title:
            await bot.send_message(chat_id=message.chat.id,
                                   text='Ищем события...', reply_markup=ReplyKeyboardRemove())
            await asyncio.sleep(1)
            await bot.send_message(chat_id=message.chat.id,
                                   text='События, в которых вы участвуете',
                                   reply_markup=kb3(events_id_title))
            await AdminState.show_list_events.set()
        else:
            await bot.send_message(chat_id=message.chat.id,
                                   text='Вы пока не участвуете ни в одном событии',
                                   reply_markup=kb0())
            await AdminState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# выбрал событие
async def admin_choose_my_event(callback: types.CallbackQuery, state: FSMContext):
    try:
        event_id = int(callback.data.split('_')[-1])
        await callback.message.delete()
        if event_id == 0:
            await state.finish()
            await callback.message.answer('Выберите пункт', reply_markup=kb0())
            await AdminState.in_game.set()
        else:
            text = get_text(event_id, callback.from_user.id)
            await state.update_data(ADMEV_ID=event_id)  # сохраняем данные
            await bot.send_message(chat_id=callback.from_user.id, text=text,
                                   reply_markup=kb1())
            await AdminState.make_choose.set()
    except Exception as err:
        logger.info(f'{err}')


# отказывается от участия
async def admin_refuse_participate(callback: types.CallbackQuery, state: FSMContext):
    try:
        event_id = await state.get_data('ADMEV_ID')  # получаем данные
        await callback.message.delete()
        if refuse_user(callback.from_user.id, event_id['ADMEV_ID']):
            await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии')
            await state.reset_data()
            await admin_take_part_events(callback.message, state)
            await AdminState.in_game.set()
        else:
            await bot.send_message(chat_id=callback.from_user.id, text='Вы не были удалены из события, '
                                                                       'обратитесь к разработикам - @slim1305')
            await state.reset_data()
            await admin_take_part_events(callback.message, state)
            await AdminState.in_game.set()
            logger.info('Не удалось удалить участника')
    except Exception as err:
        logger.info(f'{err}')


# назад к списку категорий
async def admin_beetwen_my_list_events(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        await admin_take_part_events(callback.message, state)
        await AdminState.show_categories.set()
    except Exception as err:
        logger.info(f'{err}')


# Могу поучаствовать
# показываем категории, если они есть
# будет работать только для приватных чатов
async def admin_all_category_list(message: types.Message, state: FSMContext):
    try:
        categories_list = get_categories_list(message.chat.id)
        if categories_list:
            await bot.send_message(chat_id=message.chat.id, text='Ищем категории...',
                                   reply_markup=ReplyKeyboardRemove())
            await asyncio.sleep(1)
            await bot.send_message(chat_id=message.chat.id, text='Выберите категорию',
                                   reply_markup=kb2(categories_list))
            await AdminState.show_categories.set()
        else:
            await bot.send_message(chat_id=message.chat.id, text='Пока нет событий',
                                   reply_markup=kb0())
            await AdminState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# показываем ивенты по выбранной категории
async def admin_all_list_events(callback: types.CallbackQuery, state: FSMContext):
    try:
        category = callback.data.split('_')[-1]
        await callback.message.delete()
        if category == '0':
            await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт',
                                   reply_markup=kb0())
            await AdminState.wait_for.set()
        else:
            buttons_dict = get_admin_dict_events(callback.from_user.id, category)
            if buttons_dict:
                await bot.send_message(chat_id=callback.from_user.id, text='Выберите событие',
                                       reply_markup=kb4(buttons_dict))
                await AdminState.show_events.set()
            else:
                await bot.send_message(chat_id=callback.from_user.id, text='Пока нет событий по этой категории')
                await admin_all_category_list(callback.message, state)
                await AdminState.show_categories.set()
    except Exception as err:
        logger.info(f'{err}')


# выбирает одно из событий
async def admin_choose_event(callback: types.CallbackQuery, state: FSMContext):
    try:
        event_id = int(callback.data.split('_')[-1])
        await callback.message.delete()
        if event_id == 0:
            await admin_all_category_list(callback.message, state)
            await AdminState.in_game.set()
        else:
            text = get_text(event_id, callback.from_user.id)
            await state.update_data(event_id=event_id)
            await bot.send_message(chat_id=callback.from_user.id, text=text,
                                   reply_markup=kb5())
            await AdminState.agree_disagree.set()
    except Exception as err:
        logger.info(f'{err}')


# участвует в событии
async def admin_agree(callback: types.CallbackQuery, state: FSMContext):
    try:
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
                                       text='Упс! Мы не смогли Вас добавить в участники события.')
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
    except Exception as err:
        logger.info(f'{err}')


# отказывается участвовать
async def admin_disagree(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        await state.finish()
        await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии!')
        await AdminState.in_game.set()
        await admin_all_category_list(callback.message, state)
    except Exception as err:
        logger.info(f'{err}')


# Установить часовой пояс
async def admin_check_city(message: types.Message, state: FSMContext):
    try:
        timezone = check_timezone(message.from_user.id)
        if timezone:
            await bot.send_message(message.from_user.id, f'Сейчас у вас установлен часовой пояс - {timezone}\n'
                                                         f'Если вы хотите его поменять - просто введите '
                                                         f'название своего города.\n'
                                                         f'Если вы не хотите его менять - нажмите '
                                                         f'"Главное меню" в меню сбоку',
                                   reply_markup=ReplyKeyboardRemove())
            await AdminState.wait_for_city.set()
        else:
            await bot.send_message(message.from_user.id, 'Пожалуйста, напишите название вашего города.\n'
                                                         'Мы используем это для установления часового пояса.',
                                   reply_markup=ReplyKeyboardRemove())
            await AdminState.wait_for_city.set()
    except Exception as err:
        logger.info(f'{err}')


# проверяем то, что ввёл юзер, и пытаемся установить часовой пояс
async def admin_add_timezone(message: types.Message, state: FSMContext):
    try:
        timezone_str, timezone_hours = check_city(message.text)
        if timezone_str == None:
            await message.answer("Не удалось найти такой город. "
                                 "Попробуйте написать его название латиницей "
                                 "или указать более крупный город поблизости.")
            await admin_check_city(message, state)
            await AdminState.wait_for.set()
        else:
            add_timezone(message.from_user.id, timezone_str)
            await state.finish()
            await message.answer(f"Часовой пояс установлен в {timezone_str} ({timezone_hours} от GMT)\n"
                                 f"Вы всегда можете изменить его через кнопку главного меню",
                                 reply_markup=kb0())
            await AdminState.in_game.set()
    except Exception as err:
        logger.info(f'{err}')

    ########################################################################################
    # только для админов


# Добавить инициатора
# установить инициатора
async def admin_add_initiator(message: types.Message, state: FSMContext):
    try:
        await message.answer(text="Напиши никнейм инициатора "
                                  "в формате @ник")
        await AdminState.wait_for_nick.set()
    except Exception as err:
        logger.info(f'{err}')


# проверяем ник, добавляем
async def admin_check_nickname(message: types.Message, state: FSMContext):
    try:
        user_id = check_nickname(message.text)
        if user_id is False:
            await message.answer(text="Пользователь не найден, повторите ввод "
                                      "или обратитесь к разработчикам - @slim1305",
                                 reply_markup=kb0())
            await AdminState.in_game.set()
        else:
            await message.answer(text="Инициатор добавлен!",
                                 reply_markup=kb0())
            await initiator_welcome(message, user_id)
            await AdminState.in_game.set()
    except Exception as err:
        logger.info(f'{err}')


# Добавить категорию
async def admin_add_category(message: types.Message, state: FSMContext):
    try:
        await message.answer(text="Напишите название категории")
        await AdminState.wait_for_category.set()
    except Exception as err:
        logger.info(f'{err}')


# получаем название категории
async def admin_take_name_category(message: types.Message, state: FSMContext):
    try:
        category = add_category(message.text)
        if not category:
            await message.answer(text="Не удалось сохранить категорию в базе, "
                                      "попробуйте снова или обратитесь к разработчикам - @slim1305",
                                 reply_markup=kb0())
            await AdminState.in_game.set()
        else:
            await message.answer(text="Категория добавлена!",
                                 reply_markup=kb0())
            await AdminState.in_game.set()
    except Exception as err:
        logger.info(f'{err}')


def register_handlers_admins(dp: Dispatcher):
    dp.register_message_handler(admin_start_command, IsPrivateMsg(), is_admin=True,
                                commands=['start'], state=None)
    dp.register_message_handler(admin_main_menu, IsPrivateMsg(), is_admin=True,
                                commands=['main_menu'], state='*')
    dp.register_message_handler(admin_help, IsPrivateMsg(), is_admin=True,
                                commands=['help'], state='*')

    dp.register_message_handler(admin_subscribe_user, IsPrivateMsg(), is_admin=True,
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
                                       lambda callback: callback.data.startswith('adminevent_'),
                                       IsPrivateCb(), is_admin=True,
                                       state=AdminState.show_events)
    dp.register_callback_query_handler(admin_agree, IsPrivateCb(), is_admin=True, text='adm_agree',
                                       state=AdminState.agree_disagree)
    dp.register_callback_query_handler(admin_disagree, IsPrivateCb(), is_admin=True, text='adm_disagree',
                                       state=AdminState.agree_disagree)

    dp.register_message_handler(admin_check_city, IsPrivateMsg(), is_admin=True,
                                text='Установить часовой пояс', state='*')
    dp.register_message_handler(admin_add_timezone, IsPrivateMsg(), is_admin=True,
                                state=AdminState.wait_for_city,
                                content_types=types.ContentTypes.TEXT)

    ###############
    dp.register_message_handler(admin_add_initiator, is_admin=True,
                                text='Добавить инициатора', state='*')
    dp.register_message_handler(admin_check_nickname, IsPrivateMsg(), content_types=types.ContentTypes.TEXT,
                                is_admin=True, state=AdminState.wait_for_nick)

    dp.register_message_handler(admin_add_category, is_admin=True,
                                text='Добавить категорию', state='*')
    dp.register_message_handler(admin_take_name_category, IsPrivateMsg(), content_types=types.ContentTypes.TEXT,
                                is_admin=True, state=AdminState.wait_for_category)
