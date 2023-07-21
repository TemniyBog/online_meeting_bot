from sqlalchemy import create_engine, Column, ForeignKey, Integer, BigInteger, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

from connecting_bot.my_bot.db.db_connect import DB_PATH

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    user_name = Column(String(33), unique=True)
    user_id = Column(BigInteger, primary_key=True, index=True, nullable=False)
    subscribe = Column(Boolean, unique=False, default=False)
    initiator1 = relationship('Initiator', backref='user', uselist=False, cascade="all, delete-orphan")
    participants = relationship('Participant', backref='participant1', uselist=False)


class Initiator(Base):
    __tablename__ = 'initiators'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), unique=True, nullable=False)
    event1 = relationship('Event', backref='initiator', single_parent=True, cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('initiators.user_id'), unique=False, nullable=False)
    category = Column(String(50), ForeignKey('categories.title'), nullable=False)
    title = Column(String(50))
    about = Column(String(500))
    datetime = Column(DateTime)
    number_of_participants = Column(Integer)
    events2 = relationship('Participant', backref='event', single_parent=True, cascade="all, delete-orphan")


class Participant(Base):
    __tablename__ = 'participants'
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id'), unique=False, nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), unique=False, nullable=False, index=True)

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(50), nullable=False, unique=True)
    event_connect = relationship('Event', backref='connect_event', uselist=False, cascade="all, delete-orphan")

class Meeting(Base):
    __tablename__ = 'meetings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(100), nullable=False, unique=True)
    client_id = Column(String(100), nullable=False, unique=True)
    client_secret = Column(String(100), nullable=False, unique=True)
    meeting_id = Column(BigInteger, default=None)


if __name__ == '__main__':
    engine = create_engine(DB_PATH)
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)
    session.commit()


def create_tables():
    engine = create_engine(DB_PATH)
    Session = sessionmaker(bind=engine)
    session = Session()
    Base.metadata.create_all(engine)
    session.commit()
