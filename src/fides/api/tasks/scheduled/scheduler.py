from typing import Any, Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Use a 5 minute grace period for daily jobs to mitigate job misfires
DEFAULT_DAILY_JOBS_GRACE_PERIOD = 300


def _is_daily_or_less_frequent(trigger_args: dict) -> bool:
    """A cron job with a specific hour value runs at most once per day."""
    hour = trigger_args.get("hour")
    return hour is not None and "*" not in str(hour) and "/" not in str(hour)


class _DailyJobGracePeriodMixin:
    """Auto-applies a misfire grace period to daily (or less frequent) cron jobs.

    APScheduler's default misfire_grace_time is 1 second, meaning that if the
    scheduler's event loop or thread pool is even slightly delayed past the
    scheduled time, the job is silently skipped. For daily jobs, this is far too
    tight — a brief GC pause, CPU throttle, or thread contention can cause a
    missed execution that won't retry for another 24 hours.

    This mixin intercepts add_job calls and automatically applies a generous
    grace period to any cron job that runs daily or less frequently (detected by
    a specific ``hour`` value in the trigger args). Callers can still override
    by passing ``misfire_grace_time`` explicitly.
    """

    def add_job(
        self,
        func: Callable,
        trigger: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        if (
            trigger == "cron"
            and "misfire_grace_time"
            not in kwargs  # respect user-specified grace period
            and _is_daily_or_less_frequent(kwargs)
        ):
            kwargs["misfire_grace_time"] = DEFAULT_DAILY_JOBS_GRACE_PERIOD
        return super().add_job(func, trigger=trigger, **kwargs)  # type: ignore[misc]


class GracefulBackgroundScheduler(_DailyJobGracePeriodMixin, BackgroundScheduler):
    """BackgroundScheduler with automatic misfire grace for daily cron jobs."""


class GracefulAsyncIOScheduler(_DailyJobGracePeriodMixin, AsyncIOScheduler):
    """AsyncIOScheduler with automatic misfire grace for daily cron jobs."""


scheduler = GracefulBackgroundScheduler()
async_scheduler = GracefulAsyncIOScheduler()


def create_cron_trigger(cron_expression: str, timezone: str) -> CronTrigger:
    return CronTrigger.from_crontab(cron_expression, timezone=timezone)
