import datetime

import geopy
import pytz
import requests
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base

from connecting_bot.my_bot.db.db_connect import session
from connecting_bot.my_bot.db.db_sqlalchemy import User, Initiator, Event, Participant, Category, Meeting

Base = declarative_base()


# заносим юзера в базу
def register_user(message):
    username = message.from_user.username if message.from_user.username else None
    user = User(user_id=int(message.from_user.id), user_name=username)
    session.add(user)
    try:
        session.commit()
        logger.info(f'Пользователь {user.user_name} успешно сохранён в базе')
    except IntegrityError:
        session.rollback()  # откатываем session.add(user)
        logger.info(f'Пользователь {user.user_name} уже есть в базе')


# подписываем юзера
def subscribe_user(user_id):
    user = session.query(User).filter(User.user_id == user_id).first()
    user.subscribe = True
    try:
        session.commit()
        logger.info(f'Пользователь {user.user_name} успешно подписан на рассылку')
    except IntegrityError:
        session.rollback()  # откатываем session.add(user)
        logger.info(f'Не удалось подписать пользователя {user.user_name}')


# отписываем юзера
def delete_user(user_id):
    user = session.query(User).filter(User.user_id == user_id).first()
    user.subscribe = False
    try:
        session.commit()
        logger.info(f'user {user.user_name} подписка False')
    except IntegrityError:
        session.rollback()  # откатываем session.add(user)
        logger.info(f'Не удалось {user.user_name} подписка False')


# ищем инициатора
def check_nickname(user_name):
    user_name = user_name.strip()
    if user_name[0] == '@':
        user_name = user_name[1:]
    user = session.query(User).filter(User.user_name == user_name).first()
    if user is None:
        return False
    else:
        initiator = Initiator(user_id=user.user_id)
        session.add(initiator)
        try:
            session.commit()
            logger.info(f'Успешно создан объект в базе инициатор {user.user_name}')
        except IntegrityError:
            session.rollback()  # откатываем session.add(user)
            logger.info(f'Не удалось создать объект в базе инициатор {user.user_name}')
        return int(user.user_id)


# проверяем дату
def check_date(t):
    b = None
    for x in range(len(t)):
        if not t[x].isdigit():
            b = t[x]
            a = x
    if b != None:
        r = t.split(b)
        t = r[0] + '-' + r[1]
        try:
            datetime.datetime.strptime(t, '%d-%m')
            return t
        except:
            return None
    else:
        return None


# проверяем время
def check_time(t):
    b = None
    for x in range(len(t)):
        if not t[x].isdigit():
            b = t[x]
            a = x
    if b != None:
        r = t.split(b)
        t = r[0] + ':' + r[1]
    else:
        t = t[:-2] + ':' + t[len(t) - 2:]
    try:
        datetime.datetime.strptime(t, '%H:%M')
        return t

    except:
        return None


# сохраняем событие
def save_event(user_id, category, title, about, date, time, number):
    try:
        t = date + ' ' + time
        dt = datetime.datetime.strptime(t, '%d-%m-%Y %H:%M')  # дата без часового пояса
        initiator = session.query(User).filter(User.user_id == user_id).first()
        initiator_tz = pytz.timezone(initiator.time_zone)  # таймзона инициатора
        event_with_tz = initiator_tz.localize(dt)  # время ивента с часовым
        utc_tz = pytz.timezone('UTC')
        utc_event = event_with_tz.astimezone(utc_tz)  # время ивента по utc
        utc_now = datetime.datetime.now(pytz.timezone('UTC'))  # текущее время по utc
        if (utc_event - datetime.timedelta(hours=6)) > utc_now:
            logger.info(f'Время ещё не прошло')
            utc_event_str = datetime.datetime.strftime(utc_event,
                                                       '%d-%m-%Y %H:%M')  # преобразовываем обратно в строку, потому что БД ебёт мозги и сама меняет часовой пояс у utc_event
            event = Event(user_id=user_id, category=str(category), title=str(title),
                          about=str(about), date_time=utc_event_str, number_of_participants=int(number))
            try:
                session.add(event)
                session.commit()
                logger.info(f'Ивент {event.id} успешно добавлен в базу')
                utc_event = utc_event.strftime('%d-%m-%Y %H:%M')
                return event.id, utc_event
            except Exception as err:
                session.rollback()  # откатываем session.add(user)
                logger.info(f'Какие-то проблемы с добавлением ивента {title}\n{err}')
                return False, False
        else:
            logger.info(f'Время уже прошло')
            return False, False
    except Exception as err:
        logger.info(f'save event\n{err}')
        return False, False


# получаем текст события
def get_text(event_id, user_id):
    try:
        event = session.query(Event).filter(Event.id == event_id).first()
        user = session.query(User).filter(User.user_id == user_id).first()
        dt_utc = event.date_time
        utc_tz = pytz.timezone('UTC')
        utc_event = utc_tz.localize(dt_utc)  # дата ивента в utc
        tz = pytz.timezone(user.time_zone)  # таймзона usera
        our_tz_date = utc_event.astimezone(tz)
        utc_event_str = datetime.datetime.strftime(our_tz_date, '%d-%m в %H:%M')
        return f'Событие {event.title}\nВ категории {event.category}\n{event.about}\n' \
               f'Состоится {utc_event_str}'
    except Exception as err:
        logger.info(f'Какие-то проблемы с поиском ивента {event_id} в базе\nERROR {err}')


# получаем список юзеров по ивенту
def get_users(event_id):
    user_id_list = list()
    try:
        users = session.query(User).filter(User.subscribe == True).all()
        for user in users:
            if session.query(Event).filter(Event.id == event_id,
                                           Event.user_id == user.user_id).first() == None:
                user_id_list.append(user.user_id)
            else:
                logger.info(f'По ивенту {event_id} юзер {user.user_id} является инициатором')
        if user_id_list:
            logger.info(f'СПИСОК ЮЗЕРОВ --- {user_id_list}')
            return user_id_list
        else:
            return None
    except Exception:
        logger.info('Какие-то проблемы с поиском юзеров в таблице')
        return None


# добавляем пользователя в участники события
def add_participant(user_id, event_id):
    try:
        event = session.query(Event).filter(Event.id == event_id).first()
        if user_id != event.user_id:
            participant = Participant(user_id=user_id, event_id=event_id)
            session.add(participant)
            session.commit()
            logger.info(f'Пользователь добавлен в базу {participant.participant1.user_name}')
            return True
        else:
            logger.info(f'Пользователь {event.initiator.user.user_name} является инициатором '
                        f'и не был добавлен в участники')
            return False
    except Exception as err:
        session.rollback()
        logger.info(f'Error Пользователя {user_id} в ивент {event_id} не удалось добавить в базу\n{err}')
        return False


# проверяем количество участников по ивенту
def check_count_of_participants(event_id):
    try:
        event = session.query(Event).filter(Event.id == event_id).first()
        count_of_participants = event.number_of_participants
        count_of_participants_in_table = session.query(Participant).filter(Participant.event_id == event_id).count()
        if count_of_participants_in_table < count_of_participants:
            return True
        else:
            return False
    except Exception:
        logger.info(f'По такому айди {event_id} ивент не найден')
        return False


# получаем список участников по ивенту
def get_participants(event_id):
    id_list = list()
    try:
        participants = session.query(Participant).filter(Participant.event_id == event_id).all()
        for x in participants:
            id_list.append(x.user_id)
        logger.info(f'Список участников по {event_id} event успешно достали')
        return id_list
    except Exception:
        logger.info(f'Не удалось достать список участников по {event_id} event')
        return False


# получаем текст напоминания о событии
def get_text_for_participants(event_id, user_id):
    try:
        event = session.query(Event).filter(Event.id == event_id).first()
        dt_utc = event.date_time  # дата ивента в utc
        utc_tz = pytz.timezone('UTC')
        utc_datetime = utc_tz.localize(dt_utc)
        user = session.query(User).filter(User.user_id == user_id).first()
        tz = pytz.timezone(user.time_zone)  # таймзона usera
        # Конвертировать время в новый часовой пояс
        our_date = utc_datetime.astimezone(tz)
        # Формат даты в новом часовом поясе
        format_date = our_date.strftime("%d-%m в %H:%M")

        logger.info(f'event {event.id} успешно найден в базе')
        return f'Напоминаю, что {format_date} состоится:\nИвент {event.title}\n' \
               f'В категории {event.category}\n{event.about}'
    except Exception as err:
        logger.info(f'Какие-то проблемы с поиском ивента {event_id} в базе\n{err}')
        return False


# события для юзера
def get_dict_events(user_id, category):
    user_id = int(user_id)
    buttons_dict = dict()
    try:
        datetime_now = datetime.datetime.now(pytz.timezone('UTC'))
        events = session.query(Event).filter(Event.category == category).all()
        if events:
            for event in events:
                tz = pytz.timezone("UTC")
                event_time = tz.localize(event.date_time)
                if event_time > datetime_now:
                    logger.info(f'Время по событию {event.id} подходит')
                    if event.user_id != user_id:
                        logger.info(f'{user_id} не является инициатором')
                        participant = session.query(Participant).filter(Participant.event_id == event.id,
                                                                        Participant.user_id == user_id).first()
                        if participant == None:
                            logger.info(f'{user_id} не является участником')
                            button = 'event_' + str(event.id)
                            buttons_dict[event.title] = button
            if buttons_dict:
                logger.info(f'События в количестве {len(buttons_dict)} '
                            f'будут предложены пользователю')
                return buttons_dict
        else:
            logger.info(f'Нет событий на данный момент')
            return False
    except Exception as err:
        logger.info(f'Ошибка с составлением списка событий\n{err}')
        return False


# список событий для инициатора
def get_user_dict_events(user_id, category):
    buttons_dict = dict()
    try:
        now = datetime.datetime.now(pytz.timezone('UTC'))
        events = session.query(Event).filter(Event.category == category).all()
        if events:
            for event in events:
                tz = pytz.timezone("UTC")
                event_time = tz.localize(event.date_time)
                if event_time > now:
                    if event.user_id != user_id:
                        participant = session.query(Participant).filter(Participant.event_id == event.id,
                                                                        Participant.user_id == user_id).first()
                        if participant == None:
                            button = 'usevent_' + str(event.id)
                            buttons_dict[event.title] = button
            if buttons_dict:
                logger.info(f'События в количестве {len(buttons_dict)} '
                            f'будут предложены пользователю')
                return buttons_dict
        else:
            logger.info(f'Нет событий на данный момент')
            return False
    except Exception:
        logger.info(f'Ошибка с составлением списка событий')
        return False


# список событий для админов
def get_admin_dict_events(user_id, category):
    buttons_dict = dict()
    try:
        now = datetime.datetime.now(pytz.timezone('UTC'))
        events = session.query(Event).filter(Event.category == category).all()
        if events:
            for event in events:
                tz = pytz.timezone("UTC")
                event_time = tz.localize(event.date_time)
                if event_time > now:
                    logger.info(f'Время по событию {event.id} подходит')
                    if event.user_id != user_id:
                        logger.info(f'{user_id} не является инициатором')
                        participant = session.query(Participant).filter(Participant.event_id == event.id,
                                                                        Participant.user_id == user_id).first()
                        if participant == None:
                            logger.info(f'{user_id} не является участником')
                            button = 'adminevent_' + str(event.id)
                            buttons_dict[event.title] = button
            if buttons_dict:
                logger.info(f'События в количестве {len(buttons_dict)} '
                            f'будут предложены пользователю')
                return buttons_dict
        else:
            logger.info(f'Нет событий на данный момент')
            return False
    except Exception:
        logger.info(f'Ошибка с составлением списка событий')
        return False


# проверям, является ли он инциатором
def is_he_initiator(user_id):
    try:
        initiator = session.query(Initiator).filter(Initiator.user_id == user_id).first()
        if initiator != None:
            logger.info(f'Юзер {user_id} найден в базе иницаторов')
            return True
        else:
            logger.info(f'Юзер {user_id} не найден в базе иницаторов')
            return False
    except Exception:
        logger.info(f'Ошибка с поиском юзера {user_id} в базе иницаторов')
        return False


# составляем список инициаторов
def initiators_list():
    i_list = list()
    try:
        initiators = session.query(Initiator).all()
        for each in initiators:
            i_list.append(each.user_id)
        logger.info('Составили список инициаторов')
        return i_list
    except Exception:
        logger.info('Ошибка с составлением списка инициаторов')


# получаем список категорий
def get_categories_list(user_id):
    categories_list = list()

    try:
        categories = session.query(Category).all()
        if categories:
            for each in categories:
                if get_dict_events(user_id, each.title):
                    categories_list.append(each.title)
            if categories_list:
                logger.info(f'Нашли {len(categories_list)} категорий в базе')
                return categories_list
        else:
            logger.info(f'Не нашли категории')
            return False
    except Exception as err:
        logger.info(f'Ошибка с поиском категорий в базе\n{err}')
        return False


# получаем словарь ивентов, в которых участвует юзер
def my_events(user_id):
    events_id_title = dict()
    try:
        participant_list = session.query(Participant).filter(Participant.user_id == user_id).all()
        if participant_list:
            for each in participant_list:
                now_dt = datetime.datetime.now(pytz.timezone('UTC'))
                tz = pytz.timezone("UTC")
                event_time = tz.localize(each.event.date_time)
                if event_time > now_dt:
                    logger.info(f'Время по событию {each.event.title} подходит')
                    events_id_title[each.event_id] = each.event.title
            if events_id_title:
                return events_id_title
            else:
                return False
        else:
            return False
    except Exception as err:
        logger.info(f'Ошибка с поиском ивентов, в которых участвует юзер, в базе\n{err}')
        return False


# удаляем участника из таблицы участников
def refuse_user(user_id, event_id):
    try:
        participant = session.query(Participant).filter(Participant.user_id == int(user_id),
                                                        Participant.event_id == int(event_id)).first()
        if participant != None:
            session.delete(participant)
            session.commit()
            logger.info(f'Участник {user_id} по {event_id} успешно удалён')
            return True
        else:
            logger.info(f'Участник {user_id} по {event_id} не был найден')
            return False
    except Exception:
        session.rollback()
        logger.info(f'С участником {user_id} по event {event_id} возникла проблема')
        return False


# показываем ивенты для инициатора
def show_ini_events(user_id):
    events_id_title = dict()
    try:
        events_list = session.query(Event).filter(Event.user_id == user_id).all()
        if events_list != None:
            for each in events_list:
                now = datetime.datetime.now(pytz.timezone('UTC'))
                tz = pytz.timezone("UTC")
                event_time = tz.localize(each.date_time)
                if event_time > now:
                    logger.info(f'Время по событию {each.title} подходит')
                    events_id_title[each.id] = each.title
            if events_id_title:
                logger.info('Всё чётко по инициаторским ивентам')
                return events_id_title
            else:
                return False
    except Exception as err:
        logger.info(f'Ошибка с поиском инициаторских ивентов\n{err}')
        return False


# удаляем ивент инициатора
def delete_initiator_event(user_id, event_id):
    try:
        event = session.query(Event).filter(Event.user_id == user_id, Event.id == event_id).first()
        session.delete(event)
        session.commit()
        logger.info('Ивент успешно удалён')
        return True
    except Exception:
        session.rollback()
        logger.info('Ивент не был успешно удалён')
        return False


# получаем список всех категорий
def categories_list():
    categories_list = list()
    try:
        categories = session.query(Category).all()
        if categories != None:
            for each in categories:
                categories_list.append(each.title)
            return categories_list
        else:
            logger.info('Нет категорий')
            return False
    except Exception:
        logger.info('Проблема с составлением списка категорий')
        return False


# добавляем категорию
def add_category(title):
    category = Category(title=str(title))
    session.add(category)
    try:
        session.commit()
        logger.info(f'Категория {category.title} успешно сохранена в базе')
        return True
    except IntegrityError:
        session.rollback()  # откатываем session.add(user)
        logger.info(f'Категория {category.title} не удалось сохранить в базе')
        return False


# получить данные АПИ зума для создания ивента
def get_zoom_data():
    try:
        meeting = session.query(Meeting).filter(Meeting.meeting_id == None).first()
        return meeting.account_id, meeting.client_id, meeting.client_secret
    except Exception as err:
        print('Oshibkaaaa' + str(err))


# получить данные АПИ для удаления
def get_zoom_data_for_delete(meeting_id):
    try:
        meeting = session.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        return meeting.account_id, meeting.client_id, meeting.client_secret
    except Exception as err:
        print(f'Oshibkaaaa\n{err}')


# добавить айди митинга в таблицу
def set_zoom_id(account_id, meeting_id):
    try:
        meeting = session.query(Meeting).filter(Meeting.account_id == account_id).first()
        meeting.meeting_id = meeting_id
        session.add(meeting)
        session.commit()
        logger.info('Добавили айди митинга в таблицу')
    except Exception as err:
        session.rollback()  # откатываем session.add
        print(err)


# поставить None в таблицу к митингу
def set_none(id):
    try:
        meeting = session.query(Meeting).filter(Meeting.meeting_id == id).first()
        meeting.meeting_id = None
        session.add(meeting)
        session.commit()
        logger.info('Успешно поставили None в таблице митингу')
    except Exception as err:
        session.rollback()  # откатываем session.ad
        logger.info(f'Error set_none\n{err}')


# проверяем, установлен ли у юзера часовой пояс
def check_timezone(user_id):
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user == None:
            return False
        else:
            return user.time_zone
    except Exception as err:
        logger.info(f"Error:\n{err}")
        return False


# добавить в базу часовой пояс
def add_timezone(user_id, timezone):
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        user.time_zone = timezone
        session.add(user)
        session.commit()
        logger.info(f"Успешно добавили часовой пояс")
    except Exception as err:
        session.rollback()  # откатываем session.add(user)
        logger.info(f"Error при добавлении часового пояса:\n{err}")


# устанавливаем часовой пояс
def check_city(city):
    try:
        geo = geopy.geocoders.Nominatim(user_agent="govnoezha@rambler.ru")
        location = geo.geocode(city)  # получаем локацию
        if location is None:
            return None, None
        else:
            url = f'http://api.geonames.org/timezoneJSON?lat={location.latitude}&lng={location.longitude}&username=KrotBegemot'
            r = requests.post(url=url)
            timezone_str = r.json()['timezoneId']  # получаем название часового пояса
            tz = pytz.timezone(timezone_str)
            tz_info = datetime.datetime.now(tz=tz).strftime("%z")  # получаем смещение часового пояса
            tz_info = tz_info[0:3] + ":" + tz_info[3:]  # приводим к формату ±ЧЧ:ММ
            return timezone_str, tz_info
    except Exception as err:
        logger.info(f'{err}')


# проверить иницатора на количество уже созданных им ивентов
def check_ini_events(user_id):
    count = 0
    try:
        events = session.query(Event).filter(Event.user_id == user_id).all()
        for each in events:
            tz = pytz.timezone("UTC")
            our_dt = tz.localize(each.date_time)
            now = datetime.datetime.now(pytz.timezone('UTC'))
            if our_dt > now:
                count += 1
        if count < 4:
            return True
        else:
            return False
    except Exception as err:
        logger.info(f'Проверка инициатора на количество ивентов выдала ошибку\n{err}')
        return False


# текст о событии для инициатора с количеством уже записавшихся на него будущих участников
def get_text_for_initiator(event_id, user_id):
    try:
        event = session.query(Event).filter(Event.id == event_id).first()
        utc_tz = pytz.timezone('UTC')
        dt_utc = utc_tz.localize(event.date_time)  # дата ивента в utc
        user = session.query(User).filter(User.user_id == user_id).first()
        tz = pytz.timezone(user.time_zone)  # таймзона usera
        our_date = dt_utc.astimezone(tz)
        format_date = our_date.strftime("%d-%m в %H:%M")
        part_count = session.query(Participant).filter(Participant.event_id == event_id).count()
        return f'Событие {event.title}\nВ категории {event.category}\n{event.about}\n' \
               f'Состоится {format_date}\n' \
               f'На данный момент на мероприятие записался(-ось) {part_count} человек.'
    except Exception as err:
        logger.info(f'Какие-то проблемы с поиском ивента {event_id} в базе\nERROR {err}')
