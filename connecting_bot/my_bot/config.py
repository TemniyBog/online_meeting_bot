import os

from dotenv import load_dotenv, dotenv_values

load_dotenv()

BOT_TOKEN = str(os.getenv('BOT_TOKEN'))

PGHOST = str(os.getenv('PGHOST'))
PGPASSWORD = str(os.getenv('PGPASSWORD'))
PGDATABASE = str(os.getenv('PGDATABASE'))
PGUSER = str(os.getenv('PGUSER'))
PGPORT = str(os.getenv('PGPORT'))

REDIS_HOST = str(os.getenv('REDIS_HOST'))
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_DB = int(os.getenv('REDIS_DB'))
REDIS_PASSWORD = str(os.getenv('REDIS_PASSWORD'))

GEONAMES_NICK= str(os.getenv('GEONAMES_NICK'))

ADMIN = dotenv_values().get('ADMIN').split(',')
