import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from connecting_bot.my_bot.bot_spec import scheduler, bot
from connecting_bot.my_bot.config import BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_DB, ADMIN
from connecting_bot.my_bot.db.db_sqlalchemy import create_tables
from connecting_bot.my_bot.filters.admin import AdminFilter
from connecting_bot.my_bot.handlers.admins import register_handlers_admins
from connecting_bot.my_bot.handlers.initiators import register_handlers_initiators
from connecting_bot.my_bot.handlers.users import register_handlers_users


# def register_all_middlewares(dp):
#     dp.setup_middleware(...)

def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)

def register_all_handlers(dp):
    register_handlers_admins(dp)
    register_handlers_initiators(dp)
    register_handlers_users(dp)


async def main():
    logging.basicConfig(level=logging.DEBUG,
                        format=u"%(filename)s:%(lineno)d #%(asctime)s %(levelname)s %(message)s")
    bot = Bot(token=BOT_TOKEN)
    storage = RedisStorage2(REDIS_HOST, REDIS_PORT, REDIS_DB)
    dp = Dispatcher(bot, storage=storage)
    # job_stores = {
    #     "default": RedisJobStore(
    #         jobs_key="dispatched_trips_jobs",
    #         run_times_key="dispatched_trips_running",
    #         host=REDIS_HOST,
    #         db=REDIS_DB,
    #         port=REDIS_PORT
    #     )
    # }
    #
    # scheduler = ContextSchedulerDecorator(AsyncIOScheduler(jobstores=job_stores))
    # scheduler.ctx.add_instance(bot, declared_class=Bot)
    #
    # console_out = logging.StreamHandler()
    #
    #
    # bot['scheduler'] = scheduler
    create_tables()

    # register_all_middlewares(dp)
    register_all_filters(dp)
    register_all_handlers(dp)

    try:
        scheduler.start()
        await dp.start_polling()

    finally:
        for each in ADMIN:
            await bot.send_message(chat_id=each,
                                   text='Бот выключен')
        await dp.bot.session.close()
        await dp.storage.close()
        await dp.storage.wait_closed()
    



if __name__ == '__main__':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error('Бот завершил свою работу')

