import os
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import logging
from connecting_bot.my_bot.config import PGUSER, PGHOST, PGPASSWORD, PGDATABASE

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
console_out = logging.StreamHandler()


DB_PATH = f'postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:5432/{PGDATABASE}'


engine = create_engine(DB_PATH)
session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()
Base.query = session.query_property()

# def catch_session(func):
#     """Decorator for Session"""
#     def wrapper(self, *args, **kwargs):
#         print(f"Try calling db func: {func.__name__}")
#         result = func(self, *args, **kwargs)
#         try:
#             self.session.commit()
#             print(f"Success calling db func: {func.__name__}\n")
#         except SQLAlchemyError as e:
#             print(f"Error - {e}\n")
#             self.session.rollback()
#         finally:
#             self.session.close()
#         return result
#     return wrapper

# def create_dbsession(db_path=None, **kwargs):
#     db_path = db_path or DB_PATH
#     engine = create_engine(f'postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}/{PGDATABASE}', echo=True)
#     SessionClass = sessionmaker(bind=engine)
#     return SessionClass()