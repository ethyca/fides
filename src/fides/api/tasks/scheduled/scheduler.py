from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()
async_scheduler = AsyncIOScheduler()


def create_cron_trigger(cron_expression: str, timezone: str) -> CronTrigger:
    return CronTrigger.from_crontab(cron_expression, timezone=timezone)
