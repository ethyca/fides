import re
from typing import Any, Callable, Optional, Union

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Use a 5 minute grace period for daily jobs to mitigate job misfires
DEFAULT_DAILY_JOBS_GRACE_PERIOD = 300

# Matches a bare non-negative integer with optional surrounding whitespace,
# rejecting cron syntax like ``*``, ``*/6``, ``2,14``, ``0-3``, etc.
_SINGLE_INT_RE = re.compile(r"^\s*\d+\s*$")


def _is_specific_hour(hour: Any) -> bool:
    """Return True if ``hour`` represents a single specific hour value.

    A single integer means the job fires at most once per day.  Wildcards
    (``*``), ranges (``0-3``), lists (``2,14``), and step expressions
    (``*/6``) all fail the regex match and are correctly rejected.
    """
    if hour is None:
        return False
    return _SINGLE_INT_RE.match(str(hour)) is not None


def _is_daily_or_less_frequent_cron(
    trigger: Union[str, CronTrigger, Any], trigger_kwargs: dict
) -> bool:
    """Determine whether a cron-based scheduled job fires at most once per day.

    Supports both the string shorthand (``trigger="cron", hour=3, …``) and
    pre-built ``CronTrigger`` instances (``trigger=CronTrigger(…)``).
    """
    if trigger == "cron":
        return _is_specific_hour(trigger_kwargs.get("hour"))
    if isinstance(trigger, CronTrigger):
        hour_field = next(f for f in trigger.fields if f.name == "hour")
        return _is_specific_hour(str(hour_field))
    return False


class _DailyJobGracePeriodMixin:
    """Auto-applies a misfire grace period to daily (or less frequent) cron jobs.

    APScheduler's default misfire_grace_time is 1 second, meaning that if the
    scheduler's event loop or thread pool is even slightly delayed past the
    scheduled time, the job is silently skipped. For daily jobs, this is far too
    tight — a brief GC pause, CPU throttle, or thread contention can cause a
    missed execution that won't retry for another 24 hours.

    This mixin intercepts add_job calls and automatically applies a generous
    grace period to any cron job that runs daily or less frequently (detected by
    a specific ``hour`` value in the trigger args or CronTrigger fields).
    Callers can still override by passing ``misfire_grace_time`` explicitly.
    """

    def add_job(
        self,
        func: Callable,
        trigger: Optional[Union[str, CronTrigger]] = None,
        **kwargs: Any,
    ) -> Any:
        if (
            "misfire_grace_time" not in kwargs  # respect user-specified grace period
            and _is_daily_or_less_frequent_cron(trigger, kwargs)
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
