from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from connecting_bot.my_bot.config import PGUSER, PGHOST, PGPASSWORD, PGDATABASE, PGPORT

DB_PATH = f'postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}'

engine = create_engine(DB_PATH)
session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()
Base.query = session.query_property()
