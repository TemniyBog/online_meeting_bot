import asyncio
import datetime

import pytz
from aiogram import types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import ReplyKeyboardRemove
from loguru import logger

from connecting_bot.my_bot.bot_spec import scheduler, bot
from connecting_bot.my_bot.db.db_commands import save_event, \
    check_time, check_date, get_text, add_participant, check_count_of_participants, \
    get_dict_events, register_user, subscribe_user, delete_user, my_events, refuse_user, \
    get_categories_list, show_ini_events, delete_initiator_event, categories_list, check_timezone, check_city, \
    add_timezone, check_ini_events, get_text_for_initiator
from connecting_bot.my_bot.filters.filters import IsPrivateCb, IsPrivateMsg, IsInitiatorMsgFilter
from connecting_bot.my_bot.keyboards.initiator_kb import kb10, kb11, kb12, kb13, kb14, kb15, kb16, kb17, kb18, kb19, \
    kb00
from connecting_bot.my_bot.misc.functions import msg_send_all, send_reminder
from connecting_bot.my_bot.states.initiator_state import InitiatorState


# старт инициаторы
async def initiator_start_command(message: types.Message, state: FSMContext):
    try:
        register_user(message)
        await message.answer(text="Привет!\nВыберите пункт",
                             reply_markup=kb10())
        await InitiatorState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# command = main menu
async def initiator_main_menu(message: types.Message, state: FSMContext):
    try:
        await state.finish()
        await message.answer('Выберите пункт', reply_markup=kb10())
        await InitiatorState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# command = help
async def initiator_help(message: types.Message, state: FSMContext):
    try:
        await message.answer('По всем интересующим Вас вопросам, а также в случае непредвиденных '
                             'ситуаций пишите в телеграм разрабочикам - @slim1305')
    except Exception as err:
        logger.info(f'{err}')


# приглашение нового инициатора
# функция без хэндлера
async def initiator_welcome(message: types.Message, user_id):
    try:
        await bot.send_message(chat_id=user_id,
                               text='Вы назначены инициатором, '
                                    'зайдите в Главное меню',
                               reply_markup=kb00())
    except Exception as err:
        logger.info(f'{err}')


# главное меню для нового инициатора
async def initiator_custom_main_menu(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        await state.finish()
        await callback.message.answer('Выберите пункт', reply_markup=kb10())
        await InitiatorState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# Подписаться
# оформить подписку юзеру
async def initiator_subscribe_user(message: types.Message, state: FSMContext):
    try:
        if not check_timezone(message.from_user.id):
            await message.answer(text="Сначала Вы должны установить ваш часовой пояс.\n"
                                      "Это можно сделать через кнопку главного меню")
            return
        subscribe_user(message.from_user.id)
        await message.answer(text="Вы подписаны на рассылку! Не включайте мьют, "
                                  "здесь не будет рекламы)")
        await InitiatorState.in_game.set()
    except Exception as err:
        logger.info(f'{err}')


# Отписаться
# отписать юзера
async def initiator_unsubscribe_user(message: types.Message, state: FSMContext):
    try:
        delete_user(message.from_user.id)
        await message.answer(text="Вы отписались от рассылки(")
        await InitiatorState.in_game.set()
    except Exception as err:
        logger.info(f'{err}')


# Уже участвую
# показываем события, в которых юзер участвует
async def initiator_take_part_events(message: types.Message, state: FSMContext):
    try:
        events_id_title = my_events(message.chat.id)
        if events_id_title:
            await bot.send_message(chat_id=message.chat.id,
                                   text='Ищем события...', reply_markup=ReplyKeyboardRemove())
            await asyncio.sleep(1)
            await bot.send_message(chat_id=message.chat.id,
                                   text='События, в которых вы участвуете',
                                   reply_markup=kb13(events_id_title))
            await InitiatorState.show_list_events.set()
        else:
            await bot.send_message(chat_id=message.chat.id,
                                   text='Вы пока не участвуете ни в одном событии',
                                   reply_markup=kb10())
            await InitiatorState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# выбрал событие
async def initiator_choose_my_event(callback: types.CallbackQuery, state: FSMContext):
    try:
        event_id = int(callback.data.split('_')[-1])
        await callback.message.delete()
        if event_id == 0:
            await state.finish()
            await callback.message.answer('Выберите пункт', reply_markup=kb10())
            await InitiatorState.in_game.set()
        else:
            text = get_text(event_id, callback.from_user.id)
            await state.update_data(EV_ID=event_id)  # сохраняем данные
            await bot.send_message(chat_id=callback.from_user.id, text=text,
                                   reply_markup=kb18())
            await InitiatorState.make_choose.set()
    except Exception as err:
        logger.info(f'{err}')


# отказывается от участия
async def initiator_refuse_participate(callback: types.CallbackQuery, state: FSMContext):
    try:
        event_id = await state.get_data('EV_ID')  # получаем данные
        await callback.message.delete()
        if refuse_user(callback.from_user.id, event_id['EV_ID']):
            await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии')
            await initiator_take_part_events(callback.message, state)
            await state.reset_data()
            await InitiatorState.in_game.set()
        else:
            await bot.send_message(chat_id=callback.from_user.id, text='Вы не были удалены из события, '
                                                                       'обратитесь к разработикам - @slim1305')
            await state.reset_data()
            await initiator_take_part_events(callback.message, state)
            await InitiatorState.in_game.set()
            logger.info('Не удалось удалить участника')
    except Exception as err:
        logger.info(f'{err}')


# назад к списку категорий
async def initiator_beetwen_my_list_events(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        await initiator_take_part_events(callback.message, state)
        await InitiatorState.show_categories.set()
    except Exception as err:
        logger.info(f'{err}')


# Могу поучаствовать
# показываем категории, если они есть
async def initiator_all_category_list(message: types.Message, state: FSMContext):
    try:
        categories_list = get_categories_list(message.chat.id)
        if categories_list:
            await message.answer(text='Ищем категории...', reply_markup=ReplyKeyboardRemove())
            await asyncio.sleep(1)
            await message.answer(text='Выберите категорию',
                                 reply_markup=kb12(categories_list))
            await InitiatorState.show_categories.set()
        else:
            await bot.send_message(chat_id=message.chat.id, text='Пока нет событий',
                                   reply_markup=kb10())
            await InitiatorState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# показываем ивенты по выбранной категории
async def initiator_all_list_events(callback: types.CallbackQuery, state: FSMContext):
    try:
        category = callback.data.split('_')[-1]
        await callback.message.delete()
        if category == '0':
            await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт',
                                   reply_markup=kb10())
            await InitiatorState.wait_for.set()
        else:
            buttons_dict = get_dict_events(callback.from_user.id, category)
            if buttons_dict:
                await bot.send_message(chat_id=callback.from_user.id, text='Выберите событие',
                                       reply_markup=kb11(buttons_dict))
                await InitiatorState.show_events.set()
            else:
                await bot.send_message(chat_id=callback.from_user.id, text='Пока нет событий по этой категории')
                await initiator_all_category_list(callback.message, state)
                await InitiatorState.show_categories.set()
    except Exception as err:
        logger.info(f'{err}')


# выбирает одно из событий
async def initiator_choose_events(callback: types.CallbackQuery, state: FSMContext):
    try:
        event_id = int(callback.data.split('_')[-1])
        await callback.message.delete()
        if event_id == 0:
            await initiator_all_category_list(callback.message, state)
            await InitiatorState.in_game.set()
        else:
            text = get_text(event_id, callback.from_user.id)
            await state.update_data(event_id=event_id)
            await bot.send_message(chat_id=callback.from_user.id, text=text,
                                   reply_markup=kb19())
            await InitiatorState.agree_disagree.set()
    except Exception as err:
        logger.info(f'{err}')


# участвует в событии
async def initiator_agree(callback: types.CallbackQuery, state: FSMContext):
    try:
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
    except Exception as err:
        logger.info(f'{err}')


# отказывается участвовать
async def initiator_disagree(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        await state.finish()
        await bot.send_message(chat_id=callback.from_user.id, text='Вы отказались от участия в событии!')
        await InitiatorState.in_game.set()
        await initiator_all_category_list(callback.message, state)
    except Exception as err:
        logger.info(f'{err}')


# Установить часовой пояс
async def initiator_check_city(message: types.Message, state: FSMContext):
    try:
        timezone = check_timezone(message.from_user.id)
        if timezone:
            await bot.send_message(message.from_user.id, f'Сейчас у вас установлен часовой пояс - {timezone}\n'
                                                         f'Если вы хотите его поменять - просто введите '
                                                         f'название своего города.\n'
                                                         f'Если вы не хотите его менять - нажмите '
                                                         f'"Главное меню" в меню сбоку',
                                   reply_markup=ReplyKeyboardRemove())
            await InitiatorState.wait_for_city.set()
        else:
            await bot.send_message(message.from_user.id, 'Пожалуйста, напишите название вашего города.\n'
                                                         'Мы используем это для установления часового пояса.',
                                   reply_markup=ReplyKeyboardRemove())
            await InitiatorState.wait_for_city.set()
    except Exception as err:
        logger.info(f'{err}')


# проверяем то, что ввёл юзер, и пытаемся установить часовой пояс
async def initiator_add_timezone(message: types.Message, state: FSMContext):
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
                                 reply_markup=kb10())
            await InitiatorState.in_game.set()
    except Exception as err:
        logger.info(f'{err}')


# только для инициаторов #################################
# Мои ивенты
# ивенты инициатора, которые он инициировал
async def initiator_my_events(message: types.Message, state: FSMContext):
    try:
        events_id_title = show_ini_events(message.chat.id)
        if events_id_title:
            await bot.send_message(chat_id=message.chat.id,
                                   text='Ищем события...', reply_markup=ReplyKeyboardRemove())
            await asyncio.sleep(1)
            await bot.send_message(chat_id=message.chat.id,
                                   text='События, которые вы ведёте',
                                   reply_markup=kb14(events_id_title))
            await InitiatorState.show_my_list_events.set()
        else:
            await bot.send_message(chat_id=message.chat.id, text='Вы пока не ведёте ни одного события',
                                   reply_markup=kb10())
            await InitiatorState.wait_for.set()
    except Exception as err:
        logger.info(f'{err}')


# выбрал событие
async def initiator_choose_from_my_event(callback: types.CallbackQuery, state: FSMContext):
    try:
        event_id = int(callback.data.split('_')[-1])
        await callback.message.delete()
        if event_id == 0:
            await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт',
                                   reply_markup=kb10())
            await InitiatorState.wait_for.set()
        else:
            text = get_text_for_initiator(event_id, callback.message.chat.id)
            await state.update_data(MYEV_ID=int(event_id))  # сохраняем данные
            await bot.send_message(chat_id=callback.from_user.id, text=text,
                                   reply_markup=kb17())
            await InitiatorState.make_my_choose.set()
    except Exception as err:
        logger.info(f'{err}')


# вернуться к списку событий
async def initiator_return_my_events(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        await initiator_my_events(callback.message, state)
    except Exception as err:
        logger.info(f'{err}')


# удалить событие
async def initiator_delete_my_event(callback: types.CallbackQuery, state: FSMContext):
    try:
        event_id = await state.get_data('MYEV_ID')  # получаем данные
        await callback.message.delete()
        if delete_initiator_event(callback.from_user.id, event_id['MYEV_ID']):
            await bot.send_message(chat_id=callback.from_user.id, text='Вы удалили событие')
            await state.reset_data()
            await InitiatorState.in_game.set()
            await initiator_my_events(callback.message, state)
        else:
            await bot.send_message(chat_id=callback.from_user.id, text='Событие не было удалено, '
                                                                       'обратитесь к разработикам - @slim1305')
            await state.reset_data()
            await InitiatorState.in_game.set()
            await initiator_my_events(callback.message, state)
            logger.info('Не удалось удалить участника')
    except Exception as err:
        logger.info(f'{err}')


# Добавить ивент
# вводим данные по событию
async def initiator_set_category(message: types.Message, state: FSMContext):
    try:
        if not check_ini_events(message.chat.id):
            await message.answer(text="Вы уже создатель четырёх текущих ивентов.\n"
                                      "Дождитесь, когда они пройдут, или удалите какой-либо из них, "
                                      "чтобы создать новый.")
            return
        if check_timezone(message.chat.id):
            categories_list_title = categories_list()
            if categories_list_title:
                await message.answer(text='Готовим категории...', reply_markup=ReplyKeyboardRemove())
                await asyncio.sleep(1)
                await message.answer(text='Выберите категорию',
                                     reply_markup=kb16(categories_list_title))
                await InitiatorState.set_category.set()
            else:
                await message.answer(text='Пока нет категорий, по которым можно добавить событие.\n'
                                          'Для добавления желаемой категории свяжитесь с разработчиками - @slim1305',
                                     reply_markup=kb10())
        else:
            await message.answer(text="Сначала Вы должны установить ваш часовой пояс.\n"
                                      "Это можно сделать через кнопку главного меню")
    except Exception as err:
        logger.info(f'{err}')


async def initiator_set_title(callback: types.CallbackQuery, state: FSMContext):
    try:
        category = callback.data.split('_')[-1]
        await callback.message.delete()
        if category == '0':
            await bot.send_message(chat_id=callback.from_user.id, text='Выберите пункт',
                                   reply_markup=kb10())
            await InitiatorState.wait_for.set()
        else:
            await state.update_data(CATEGORY=category)
            await bot.send_message(chat_id=callback.from_user.id, text='Напишите название события')
            await InitiatorState.set_title.set()
    except Exception as err:
        logger.info(f'{err}')


async def initiator_set_about(message: types.Message, state: FSMContext):
    try:
        await state.update_data(TITLE=message.text.strip())
        await message.answer('Введите описание события (до 500 символов)')
        await InitiatorState.set_about.set()
    except Exception as err:
        logger.info(f'{err}')


async def initiator_set_date(message: types.Message, state: FSMContext):
    try:
        await state.update_data(ABOUT=message.text)
        await message.answer('Введите дату события в формате\n'
                             'Число-Месяц')
        await InitiatorState.set_date.set()
    except Exception as err:
        logger.info(f'{err}')


async def initiator_set_time(message: types.Message, state: FSMContext):
    try:
        date = check_date(message.text)
        if date == None:
            await message.reply('Пожалуйста, введите дату события в формате\n'
                                'Число-Месяц')
            return
        date_f = date + '-2023'
        await state.update_data(DATE=date_f)
        await message.answer('Ивент можно создать минимум за 6 часов до его предполагаемого начала.\n'
                             'Введите время события по вашему часовому поясу в формате\n'
                             'Часы:Минуты')
        await InitiatorState.set_time.set()
    except Exception as err:
        logger.info(f'{err}')


async def initiator_set_number_participants(message: types.Message, state: FSMContext):
    try:
        if check_time(message.text) == None:
            await message.reply('Пожалуйста, введите время события по вашему '
                                'часовому поясу в формате\n'
                                'Часы:Минуты')
            return
        await state.update_data(TIME=check_time(message.text))
        await message.answer('Введите число участников события (максимально 100 человек)')
        await InitiatorState.set_number.set()
    except Exception as err:
        logger.info(f'{err}')


async def initiator_set_confirm(message: types.Message, state: FSMContext):
    try:
        if not message.text.isdigit() or int(message.text) > 100:
            await message.reply("Пожалуйста, введите число участников события (максимально 100 человек)")
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
                             f"Категория {category}\n{title}\n{about}\n{date} в {time}\n"
                             f"Количество участников: {number}",
                             reply_markup=kb15())
        await InitiatorState.confirm.set()
    except Exception as err:
        logger.info(f'{err}')


# последняя стадия добавления события - подтверждение события
async def initiator_add_event(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        context_data = await state.get_data()
        event_id, utc_event = save_event(callback.from_user.id,
                                         context_data['CATEGORY'],
                                         context_data['TITLE'],
                                         context_data['ABOUT'],
                                         context_data['DATE'],
                                         context_data['TIME'],
                                         context_data['NUMBER'])
        if event_id != False:
            await state.finish()
            await msg_send_all(callback, event_id)
            dt = datetime.datetime.strptime(utc_event, '%d-%m-%Y %H:%M')
            tz = pytz.timezone("UTC")
            event_time = tz.localize(dt)
            our_date = event_time - datetime.timedelta(hours=6)
            scheduler.add_job(func=send_reminder, trigger='date', run_date=our_date,
                              kwargs={'event_id': int(event_id), 'ini_id': int(callback.from_user.id),
                                      'title': str(context_data['TITLE']), 'date': utc_event},
                              misfire_grace_time=10, timezone='UTC')
            await callback.message.answer(text='Событие добавлено!',
                                          reply_markup=kb10())
            await initiator_main_menu(callback.message, state)
        else:
            await callback.message.answer(text='Событие не было опубликовано, возможно вы ввели неправильную '
                                               'дату.\n'
                                               'Повторите ввод или обратитесь к разработчикам - @slim1305',
                                          reply_markup=kb10())
            await initiator_main_menu(callback.message, state)
    except Exception as err:
        logger.info(f'{err}')


# вернулись в начало
async def initiator_return_to_start(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
        await state.reset_data()
        await initiator_set_category(callback.message, state)
    except Exception as err:
        logger.info(f'{err}')


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

    dp.register_message_handler(initiator_check_city, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                text='Установить часовой пояс', state='*')
    dp.register_message_handler(initiator_add_timezone, IsPrivateMsg(), IsInitiatorMsgFilter(),
                                state=InitiatorState.wait_for_city,
                                content_types=types.ContentTypes.TEXT)

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
