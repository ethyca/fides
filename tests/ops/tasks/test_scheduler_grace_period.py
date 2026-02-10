from unittest.mock import patch

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from fides.api.tasks.scheduled.scheduler import (
    DEFAULT_DAILY_JOBS_GRACE_PERIOD,
    GracefulAsyncIOScheduler,
    GracefulBackgroundScheduler,
    _is_daily_or_less_frequent,
)


class TestIsDailyOrLessFrequent:
    @pytest.mark.parametrize(
        "trigger_args,expected",
        [
            # Daily jobs (specific hour) → True
            ({"hour": 3, "minute": 0}, True),
            ({"hour": "2", "minute": "0"}, True),
            ({"hour": 6, "minute": 0, "timezone": "US/Eastern"}, True),
            ({"hour": 0}, True),
            # Hourly jobs (wildcard hour or no hour) → False
            ({"hour": "*"}, False),
            ({"minute": 30}, False),
            ({}, False),
            # Sub-hourly jobs → False
            ({"minute": "*/5"}, False),
            ({"minute": "*/10"}, False),
            # Every-N-hours → False
            ({"hour": "*/2"}, False),
            ({"hour": "*/6", "minute": 0}, False),
        ],
        ids=[
            "daily-int-hour",
            "daily-str-hour",
            "daily-with-timezone",
            "daily-midnight",
            "hourly-wildcard",
            "hourly-no-hour",
            "empty-args",
            "every-5-min",
            "every-10-min",
            "every-2-hours",
            "every-6-hours",
        ],
    )
    def test_is_daily_or_less_frequent(self, trigger_args, expected):
        assert _is_daily_or_less_frequent(trigger_args) == expected


class TestDailyJobGracePeriodMixin:
    @pytest.mark.parametrize(
        "trigger,add_job_kwargs,expect_grace_time",
        [
            # Daily cron: should auto-inject grace period
            (
                "cron",
                {"hour": 3, "minute": 0},
                DEFAULT_DAILY_JOBS_GRACE_PERIOD,
            ),
            (
                "cron",
                {"hour": "2", "minute": "0", "day": "*", "timezone": "US/Eastern"},
                DEFAULT_DAILY_JOBS_GRACE_PERIOD,
            ),
            # Hourly/sub-hourly cron: should NOT inject
            ("cron", {"hour": "*"}, None),
            ("cron", {"minute": "*/5"}, None),
            ("cron", {"hour": "*/2", "minute": 0}, None),
            # Non-cron trigger: should NOT inject
            ("interval", {"seconds": 300}, None),
            # Explicit override: should preserve caller's value
            ("cron", {"hour": 3, "misfire_grace_time": 60}, 60),
        ],
        ids=[
            "daily-cron-injects",
            "daily-cron-with-extras-injects",
            "hourly-cron-skipped",
            "sub-hourly-cron-skipped",
            "every-n-hours-cron-skipped",
            "interval-trigger-skipped",
            "explicit-override-preserved",
        ],
    )
    def test_background_scheduler_grace_period(
        self, trigger, add_job_kwargs, expect_grace_time
    ):
        sched = GracefulBackgroundScheduler()
        with patch.object(BackgroundScheduler, "add_job") as mock_add_job:
            sched.add_job(lambda: None, trigger=trigger, **add_job_kwargs)

            mock_add_job.assert_called_once()
            call_kwargs = mock_add_job.call_args.kwargs

            if expect_grace_time is not None:
                assert call_kwargs["misfire_grace_time"] == expect_grace_time
            else:
                assert "misfire_grace_time" not in call_kwargs

    def test_async_scheduler_grace_period(self):
        """Verify the async scheduler subclass also inherits the mixin behavior."""
        sched = GracefulAsyncIOScheduler()
        with patch.object(AsyncIOScheduler, "add_job") as mock_add_job:
            sched.add_job(lambda: None, trigger="cron", hour=3, minute=0)

            mock_add_job.assert_called_once()
            assert (
                mock_add_job.call_args.kwargs["misfire_grace_time"]
                == DEFAULT_DAILY_JOBS_GRACE_PERIOD
            )
