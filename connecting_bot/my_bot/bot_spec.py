import logging

from aiogram import Bot
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler_di import ContextSchedulerDecorator

from connecting_bot.my_bot.config import BOT_TOKEN, REDIS_HOST, REDIS_DB, REDIS_PORT

bot = Bot(token=BOT_TOKEN)
job_stores = {
        "default": RedisJobStore(
            jobs_key="dispatched_trips_jobs",
            run_times_key="dispatched_trips_running",
            host=REDIS_HOST,
            db=REDIS_DB,
            port=REDIS_PORT
        )
}

scheduler = ContextSchedulerDecorator(AsyncIOScheduler(jobstores=job_stores))
scheduler.ctx.add_instance(bot, declared_class=Bot)

console_out = logging.StreamHandler()


