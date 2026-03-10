from unittest.mock import patch

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from fides.api.tasks.scheduled.scheduler import (
    DEFAULT_DAILY_JOBS_GRACE_PERIOD,
    GracefulAsyncIOScheduler,
    GracefulBackgroundScheduler,
    _is_daily_or_less_frequent_cron,
    _is_specific_hour,
    create_cron_trigger,
)


class TestIsSpecificHour:
    @pytest.mark.parametrize(
        "hour,expected",
        [
            # Specific hours → True (daily or less frequent)
            (3, True),
            (0, True),
            ("2", True),
            (" 12 ", True),
            # Wildcards, ranges, lists, steps → False (more than once per day)
            ("*", False),
            ("*/2", False),
            ("*/6", False),
            ("2,14", False),
            ("0-3", False),
            ("1-23/2", False),
            (None, False),
        ],
        ids=[
            "int-3",
            "int-0-midnight",
            "str-2",
            "str-12-whitespace",
            "wildcard",
            "step-every-2h",
            "step-every-6h",
            "list-twice-daily",
            "range-4-times",
            "range-with-step",
            "none",
        ],
    )
    def test_is_specific_hour(self, hour, expected):
        assert _is_specific_hour(hour) == expected


class TestIsDailyOrLessFrequentCron:
    """Tests for the unified detection covering both trigger='cron' and CronTrigger instances."""

    @pytest.mark.parametrize(
        "trigger,kwargs,expected",
        [
            # String trigger — daily
            ("cron", {"hour": 3, "minute": 0}, True),
            ("cron", {"hour": "2", "minute": "0"}, True),
            # String trigger — more frequent
            ("cron", {"hour": "*"}, False),
            ("cron", {"hour": "*/2"}, False),
            ("cron", {"hour": "2,14"}, False),
            ("cron", {"hour": "0-3"}, False),
            ("cron", {"minute": "*/5"}, False),
            ("cron", {}, False),
            # Non-cron trigger
            ("interval", {"seconds": 300}, False),
            ("date", {}, False),
        ],
        ids=[
            "str-daily-int",
            "str-daily-str",
            "str-hourly-wildcard",
            "str-every-2h",
            "str-twice-daily",
            "str-range-hours",
            "str-sub-hourly-no-hour",
            "str-empty-no-hour",
            "interval-trigger",
            "date-trigger",
        ],
    )
    def test_string_and_non_cron_triggers(self, trigger, kwargs, expected):
        assert _is_daily_or_less_frequent_cron(trigger, kwargs) == expected

    @pytest.mark.parametrize(
        "cron_expression,expected",
        [
            # Daily or less frequent
            ("0 3 * * *", True),  # daily at 3 AM
            ("0 12 * * mon", True),  # weekly on Monday at noon
            ("0 0 1 * *", True),  # monthly at midnight on the 1st
            # More frequent than daily
            ("0 * * * *", False),  # every hour
            ("*/30 * * * *", False),  # every 30 minutes
            ("0 2,14 * * *", False),  # twice daily
            ("0 0-3 * * *", False),  # 4 times per day
        ],
        ids=[
            "crontrigger-daily-3am",
            "crontrigger-weekly-monday",
            "crontrigger-monthly",
            "crontrigger-every-hour",
            "crontrigger-every-30-min",
            "crontrigger-twice-daily",
            "crontrigger-range-hours",
        ],
    )
    def test_cron_trigger_instances(self, cron_expression, expected):
        trigger = CronTrigger.from_crontab(cron_expression)
        assert _is_daily_or_less_frequent_cron(trigger, {}) == expected


class TestDailyJobGracePeriodMixin:
    @pytest.mark.parametrize(
        "trigger,add_job_kwargs,expect_grace_time",
        [
            # Daily cron (string): should auto-inject grace period
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
            # Hourly/sub-hourly cron (string): should NOT inject
            ("cron", {"hour": "*"}, None),
            ("cron", {"minute": "*/5"}, None),
            ("cron", {"hour": "*/2", "minute": 0}, None),
            ("cron", {"hour": "2,14"}, None),
            ("cron", {"hour": "0-3"}, None),
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
            "twice-daily-cron-skipped",
            "range-hours-cron-skipped",
            "interval-trigger-skipped",
            "explicit-override-preserved",
        ],
    )
    def test_background_scheduler_string_trigger(
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

    @pytest.mark.parametrize(
        "cron_expression,timezone,expect_grace",
        [
            ("0 3 * * *", "US/Eastern", True),  # daily → inject
            ("0 12 * * mon", "US/Eastern", True),  # weekly → inject
            ("0 * * * *", "UTC", False),  # hourly → skip
            ("*/30 * * * *", "UTC", False),  # every 30 min → skip
            ("0 2,14 * * *", "UTC", False),  # twice daily → skip
        ],
        ids=[
            "crontrigger-daily-injects",
            "crontrigger-weekly-injects",
            "crontrigger-hourly-skipped",
            "crontrigger-sub-hourly-skipped",
            "crontrigger-twice-daily-skipped",
        ],
    )
    def test_background_scheduler_cron_trigger_instance(
        self, cron_expression, timezone, expect_grace
    ):
        sched = GracefulBackgroundScheduler()
        cron_trigger = create_cron_trigger(cron_expression, timezone)

        with patch.object(BackgroundScheduler, "add_job") as mock_add_job:
            sched.add_job(lambda: None, trigger=cron_trigger, id="test_job")

            mock_add_job.assert_called_once()
            call_kwargs = mock_add_job.call_args.kwargs

            if expect_grace:
                assert (
                    call_kwargs["misfire_grace_time"] == DEFAULT_DAILY_JOBS_GRACE_PERIOD
                )
            else:
                assert "misfire_grace_time" not in call_kwargs

    def test_cron_trigger_explicit_override_preserved(self):
        """An explicit misfire_grace_time should not be overwritten even for a CronTrigger."""
        sched = GracefulBackgroundScheduler()
        cron_trigger = create_cron_trigger("0 3 * * *", "US/Eastern")

        with patch.object(BackgroundScheduler, "add_job") as mock_add_job:
            sched.add_job(
                lambda: None,
                trigger=cron_trigger,
                id="test_job",
                misfire_grace_time=60,
            )

            assert mock_add_job.call_args.kwargs["misfire_grace_time"] == 60

    def test_async_scheduler_string_trigger(self):
        """Verify the async scheduler subclass inherits the mixin behavior."""
        sched = GracefulAsyncIOScheduler()
        with patch.object(AsyncIOScheduler, "add_job") as mock_add_job:
            sched.add_job(lambda: None, trigger="cron", hour=3, minute=0)

            mock_add_job.assert_called_once()
            assert (
                mock_add_job.call_args.kwargs["misfire_grace_time"]
                == DEFAULT_DAILY_JOBS_GRACE_PERIOD
            )

    def test_async_scheduler_cron_trigger_instance(self):
        """Verify the async scheduler handles CronTrigger instances too."""
        sched = GracefulAsyncIOScheduler()
        cron_trigger = create_cron_trigger("0 12 * * mon", "US/Eastern")

        with patch.object(AsyncIOScheduler, "add_job") as mock_add_job:
            sched.add_job(lambda: None, trigger=cron_trigger, id="test_job")

            mock_add_job.assert_called_once()
            assert (
                mock_add_job.call_args.kwargs["misfire_grace_time"]
                == DEFAULT_DAILY_JOBS_GRACE_PERIOD
            )
