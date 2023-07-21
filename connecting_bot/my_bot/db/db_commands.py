import logging
import datetime
import pytz
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker


from sqlalchemy.ext.declarative import declarative_base
import logging


from connecting_bot.my_bot.db.db_connect import session
from connecting_bot.my_bot.db.db_sqlalchemy import User, Initiator, Event, Participant, Category, Meeting

logging.basicConfig(level=logging.DEBUG)
console_out = logging.StreamHandler()

Base = declarative_base()

# заносим юзера в базу
def register_user(message):
    username = message.from_user.username if message.from_user.username else None
    user = User(user_id=int(message.from_user.id), user_name=(message.from_user.username))
    session.add(user)
    try:
        session.commit()
        logging.info(f'Пользователь {user.user_name} успешно сохранён в базе')
    except IntegrityError:
        session.rollback()  # откатываем session.add(user)
        logging.info(f'Пользователь {user.user_name} уже есть в базе')

# подписываем юзера
def subscribe_user(user_id):
    user = session.query(User).filter(User.user_id == user_id).first()
    user.subscribe = True
    try:
        session.commit()
        logging.info(f'Пользователь {user.user_name} успешно подписан на рассылку')
    except IntegrityError:
        session.rollback()  # откатываем session.add(user)
        logging.info(f'Не удалось подписать пользователя {user.user_name}')

# отписываем юзера
def delete_user(user_id):
    user = session.query(User).filter(User.user_id == user_id).first()
    user.subscribe = False
    try:
        session.commit()
        logging.info(f'user {user.user_name} подписка False')
    except IntegrityError:
        session.rollback()  # откатываем session.add(user)
        logging.info(f'Не удалось {user.user_name} подписка False')

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
            logging.info(f'Успешно создан объект в базе инициатор {user.user_name}')
        except IntegrityError:
            session.rollback()  # откатываем session.add(user)
            logging.info(f'Не удалось создать объект в базе инициатор {user.user_name}')
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
        t = t[:-2] + ':' + t[len(t)-2:]
    try:
        datetime.datetime.strptime(t, '%H:%M')
        return t

    except:
        return None

# сохраняем событие
def save_event(user_id, category, title, about, date, time, number):
    logging.info(f'{user_id}, {category}, {title}, {about}, {date}, {time}, {number}')
    t = date + ' ' + time
    dt = datetime.datetime.strptime(t, '%d-%m-%Y %H:%M')
    newTimeZone = pytz.timezone('Europe/Moscow')             # мск таймзона
    msc_offset_aware = datetime.datetime.now(tz=newTimeZone)  # получение местного московского времени
    msc = msc_offset_aware.replace(tzinfo=None)  # преобразование московского времени в utc
                                                 # без изменения самих цифр, для сравнения
    if msc < dt:
        logging.info(f'Время ещё не прошло')
        event = Event(user_id=user_id, category=str(category), title=str(title), about=str(about), datetime=dt, number_of_participants=int(number))
        try:
            session.add(event)
            session.commit()
            logging.info(f'Ивент {event.id} успешно добавлен в базу')
            return event.id, dt
        except:
            session.rollback()  # откатываем session.add(user)
            logging.info(f'Какие-то проблемы с добавлением ивента {title}')
            return False, False
    else:
        logging.info(f'Время уже прошло')
        return False, False

# получаем текст события
def get_text(event_id):
    try:
        event = session.query(Event).filter(Event.id == event_id).first()
        logging.info(f'event {event.id} успешно найден в базе')
        return f'Событие {event.title}\nВ категории {event.category}\n{event.about}\nСостоится {event.datetime}\nРассчитано на {event.number_of_participants} человек'
    except Exception:
        logging.info(f'Какие-то проблемы с поиском ивента {event_id} в базе')

# возвращаем текст события с количеством участников для инициатора
def get_ini_text(event_id):
    participants_list = get_participants(event_id)
    text1 = get_text(event_id)
    text = text1 + f'\nНа данный момент на событие записалось {len(participants_list)} человек'

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
                logging.info(f'По ивенту {event_id} юзер {user.user_id} является инициатором')
        if user_id_list:
            logging.info(f'СПИСОК ЮЗЕРОВ --- {user_id_list}')
            return user_id_list
        else:
            return None
    except Exception:
        logging.info('Какие-то проблемы с поиском юзеров в таблице')
        return None

# добавляем пользователя в участники события
def add_participant(user_id, event_id):
    try:
        event = session.query(Event).filter(Event.id == event_id).first()
        if user_id != event.user_id:
            participant = Participant(user_id=user_id, event_id=event_id)
            session.add(participant)
            session.commit()
            logging.info(f'Пользователь добавлен в базу {participant.participant1.user_name}')
            return True
        else:
            logging.info(f'Пользователь {event.initiator.user.user_name} является инициатором '
                         f'и не был добавлен в участники')
            return False
    except Exception:
        session.rollback()
        logging.info(f'Error Пользователя {user_id} в ивент {event_id} не удалось добавить в базу')
        return False

# проверяем количество участников по ивенту
def check_count_of_participants(event_id):
    try:
        event = session.query(Event).filter(Event.id == event_id).first()
        count_of_participants = event.number_of_participants
        logging.info(f'{event.id} ивент найден')
        count_of_participants_in_table = session.query(Participant).filter(Participant.event_id == event_id).count()
        if count_of_participants_in_table <= count_of_participants:
            return True
        else:
            return False
    except Exception:
        logging.info(f'По такому айди {event_id} ивент не найден')
        return False

# получаем список участников по ивенту
def get_participants(event_id):
    id_list = list()
    try:
        participants = session.query(Participant).filter(Participant.event_id == event_id).all()
        for x in participants:
            id_list.append(x.user_id)
        logging.info(f'Список участников по {event_id} event успешно достали')
        return id_list
    except Exception:
        logging.info(f'Не удалось достать список участников по {event_id} event')
        return False

# получаем текст напоминания о событии
def get_text_for_participants(event_id):
    try:
        event = session.query(Event).filter(Event.id == event_id).first()
        logging.info(f'event {event.id} успешно найден в базе')
        return f'Напоминание! Через 6 часов состоится\nСобытие {event.title}\nВ категории {event.category}\n{event.about}\n' \
               f'Состоится {event.datetime}\nРассчитано на {event.number_of_participants} человек'
    except Exception:
        logging.info(f'Какие-то проблемы с поиском ивента {event_id} в базе')
        return False

# # время напоминания про ивент за 24 часа
# def get_date(event_id):
#     try:
#         event = session.query(Event).filter(Event.id == event_id).first()
#         date = event.datetime + datetime.timedelta(minutes=1)
#         logging.info(f'{date} Всё четко со временем напоминания по ивенту {event_id}')
#         return date
#     except Exception:
#         logging.info(f'Какие-то проблемы со временем напоминания по ивенту {event_id}')
#         return False

# события для юзера
def get_dict_events(user_id, category):
    buttons_dict = dict()
    try:
        newTimeZone = pytz.timezone('Europe/Moscow')
        msc_offset_aware = datetime.datetime.now(tz=newTimeZone)
        msc = msc_offset_aware.replace(tzinfo=pytz.utc)
        logging.info('uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu')
        logging.info(f'{category}')
        events = session.query(Event).filter(Event.category == category).all()
        if events:
            logging.info(f'{events}')
            for event in events:
                event_time = event.datetime.replace(tzinfo=pytz.utc)  # объект типа "2023-12-12 02:30:00+00:00"
                if event_time > msc:
                    logging.info(f'Время по событию {event.id} подходит')
                    logging.info(f'{event_time} 00000000000000000 {msc_offset_aware}')
                    if user_id != event.user_id:
                        logging.info(f'{user_id} не является инициатором')
                        participant = session.query(Participant).filter(Participant.event_id == event.id,
                                                                        Participant.user_id == user_id).first()
                        if participant == None:
                            logging.info(f'{user_id} не является участником')
                            button = 'event_' + str(event.id)
                            buttons_dict[event.title] = button
            if buttons_dict:
                logging.info(f'События в количестве {len(buttons_dict)} '
                             f'будут предложены пользователю')
                return buttons_dict
        else:
            logging.info(f'Нет событий на данный момент')
            return False
    except Exception:
        logging.info(f'Ошибка с составлением списка событий')
        return False

# список событий для юзера или инициатора
def get_user_dict_events(user_id, category):
    buttons_dict = dict()
    try:
        newTimeZone = pytz.timezone('Europe/Moscow')
        msc_offset_aware = datetime.datetime.now(tz=newTimeZone)
        msc = msc_offset_aware.replace(tzinfo=pytz.utc)
        logging.info('uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu')
        logging.info(f'{category}')
        events = session.query(Event).filter(Event.category == category).all()
        if events:
            logging.info(f'{events}')
            for event in events:
                event_time = event.datetime.replace(tzinfo=pytz.utc)  # объект типа "2023-12-12 02:30:00+00:00"
                if event_time > msc:
                    logging.info(f'Время по событию {event.id} подходит')
                    logging.info(f'{event_time} 00000000000000000 {msc_offset_aware}')
                    if user_id != event.user_id:
                        logging.info(f'{user_id} не является инициатором')
                        participant = session.query(Participant).filter(Participant.event_id == event.id,
                                                                        Participant.user_id == user_id).first()
                        if participant == None:
                            logging.info(f'{user_id} не является участником')
                            button = 'usevent_' + str(event.id)
                            buttons_dict[event.title] = button
            if buttons_dict:
                logging.info(f'События в количестве {len(buttons_dict)} '
                             f'будут предложены пользователю')
                return buttons_dict
        else:
            logging.info(f'Нет событий на данный момент')
            return False
    except Exception:
        logging.info(f'Ошибка с составлением списка событий')
        return False

# проверям, является ли он инциатором
def is_he_initiator(user_id):
    try:
        initiator = session.query(Initiator).filter(Initiator.user_id == user_id).first()
        if initiator != None:
            logging.info(f'Юзер {user_id} найден в базе иницаторов')
            return True
        else:
            logging.info(f'Юзер {user_id} не найден в базе иницаторов')
            return False
    except Exception:
        logging.info(f'Ошибка с поиском юзера {user_id} в базе иницаторов')
        return False

# составляем список инициаторов
def initiators_list():
    i_list = list()
    try:
        initiators = session.query(Initiator).all()
        for each in initiators:
            i_list.append(each.user_id)
        logging.info('Составили список инициаторов')
        return i_list
    except Exception:
        logging.info('Ошибка с составлением списка инициаторов')

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
                logging.info(f'Нашли {len(categories_list)} категорий в базе')
                return categories_list
        else:
            logging.info(f'Не нашли категории')
            return False
    except Exception:
        logging.info(f'Ошибка с поиском категорий в базе')
        return False

# получаем словарь ивентов, в которых участвует юзер
def my_events(user_id):
    events_id_title = dict()
    try:
        participant_in_list = session.query(Participant).filter(Participant.user_id == user_id).all()
        if participant_in_list != None:
            for each in participant_in_list:
                newTimeZone = pytz.timezone('Europe/Moscow')
                msc_offset_aware = datetime.datetime.now(tz=newTimeZone)
                msc = msc_offset_aware.replace(tzinfo=pytz.utc)
                event_time = each.event.datetime.replace(tzinfo=pytz.utc)
                if event_time > msc:
                    logging.info(f'Время по событию {each.event.title} подходит')
                    events_id_title[each.event_id] = each.event.title
                    logging.info(f'We are good')
            if events_id_title:
                return events_id_title
            else:
                return False
    except Exception:
        logging.info(f'Ошибка с поиском ивентов, в которых участвует юзер, в базе')
        return False

# удаляем участника из таблицы участников
def refuse_user(user_id, event_id):
    logging.info(f'{type(user_id)}, {type(event_id)}')
    try:
        participant = session.query(Participant).filter(Participant.user_id == int(user_id),
                                                        Participant.event_id == int(event_id)).first()
        if participant != None:
            session.delete(participant)
            session.commit()
            logging.info(f'Участник {user_id} по {event_id} успешно удалён')
            return True
        else:
            logging.info(f'Участник {user_id} по {event_id} не был найден')
            return False
    except Exception:
        session.rollback()
        logging.info(f'С участником {user_id} по event {event_id} возникла проблема')
        return False

# показываем ивенты для инициатора
def show_ini_events(user_id):
    logging.info(f'{user_id}')
    events_id_title = dict()
    # try:
    events_list = session.query(Event).filter(Event.user_id == int(user_id)).all()
    logging.info('check1')
    if events_list != None:
        logging.info('check2')
        for each in events_list:
            logging.info('check3')
            newTimeZone = pytz.timezone('Europe/Moscow')
            msc_offset_aware = datetime.datetime.now(tz=newTimeZone)
            msc = msc_offset_aware.replace(tzinfo=pytz.utc)
            our = each.datetime.replace(tzinfo=pytz.utc)
            if msc < our:
                logging.info('check4')
                logging.info(f'Время по событию {each.title} подходит')
                events_id_title[each.id] = each.title
        if events_id_title:
            logging.info('Всё чётко по инициаторским ивентам')
            return events_id_title
        else:
            return False
    # except Exception:
    #     logging.info('Ошибка с поиском инициаторских ивентов')
    #     return False

# удаляем ивент инициатора
def delete_initiator_event(user_id, event_id):
    try:
        event = session.query(Event).filter(Event.user_id == user_id, Event.id == event_id).first()
        session.delete(event)
        session.commit()
        logging.info('Ивент успешно удалён')
        return True
    except Exception:
        session.rollback()
        logging.info('Ивент не был успешно удалён')
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
            logging.info('Нет категорий')
            return False
    except Exception:
        logging.info('Проблема с составлением списка категорий')
        return False

# добавляем категорию
def add_category(title):
    category = Category(title=str(title))
    logging.info('check1')
    session.add(category)
    logging.info('check2')
    try:
        logging.info('check3')
        session.commit()
        logging.info(f'Категория {category.title} успешно сохранена в базе')
        return True
    except IntegrityError:
        session.rollback()  # откатываем session.add(user)
        logging.info(f'Категория {category.title} не удалось сохранить в базе')
        return False

# получаем айди иницитора по ивенту и время минус 15 минут
def get_ini_id(event_id):
    try:
        event = session.query(Event).filter(Event.id == event_id).first()
        date = event.datetime + datetime.timedelta(minutes=2)
        title = event.title
        logging.info('Успешно получили айди иницатора и время')

        return event.user_id, date, title
    except Exception:
        logging.info('Проблема с получением айди инициатора по ивент айди')
        return None, None, None

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
        print('Oshibkaaaa' + str(err))

# добавить айди митинга в таблицу
def set_zoom_id(account_id, meeting_id):
    try:
        meeting = session.query(Meeting).filter(Meeting.account_id == account_id).first()
        meeting.meeting_id = meeting_id
        session.add(meeting)
        session.commit()
        logging.info('Добавили айди митинга в таблицу')
    except Exception as err:
        print(err)

# поставить None в таблицу к митингу
def set_none(id):
    try:
        meeting = session.query(Meeting).filter(Meeting.meeting_id == id).first()
        meeting.meeting_id = None
        session.add(meeting)
        session.commit()
        logging.info('Успешно поставили None в таблице митингу')
    except Exception as err:
        logging.info('Error set_none ' + str(err))
