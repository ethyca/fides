import math
import random
from datetime import datetime, timedelta

import pytest

from fides.api.schemas.partitioning import TimeBasedPartitioning


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _compile(expr):
    """Helper that compiles a SQLAlchemy expression to a literal SQL string."""
    return str(expr.compile(compile_kwargs={"literal_binds": True}))


def _months_between(start: datetime, end: datetime) -> int:
    """Return the number of *calendar* months between two dates (inclusive of partial last month)."""

    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day > start.day:
        months += 1
    return months


# -----------------------------------------------------------------------------
# Randomized tests (fuzz-style)
# -----------------------------------------------------------------------------


class TestRandomFixedDayWeekIntervals:
    """Generate random DAY/WEEK interval specs and assert the correct partition count."""

    RANDOM_SEED = 20240202

    @pytest.mark.parametrize("iterations", [25])
    def test_random_now_today_fixed_intervals(self, iterations):  # type: ignore[override]
        random.seed(self.RANDOM_SEED)

        for _ in range(iterations):
            # Choose NOW() or TODAY() as the dynamic anchor
            use_now = random.choice([True, False])
            anchor = "NOW()" if use_now else "TODAY()"

            # Random total duration (1-90 days)
            total_days = random.randint(1, 90)

            # Random interval (1-14 days) but not larger than duration
            interval_days = random.randint(1, min(14, total_days))

            # Normalise to weeks where divisible by 7 to exercise WEEK paths
            if interval_days % 7 == 0:
                interval_value = interval_days // 7
                interval_unit = "week" if interval_value == 1 else "weeks"
                interval_str = f"{interval_value} {interval_unit}"
            else:
                interval_str = f"{interval_days} days"

            partitioning = TimeBasedPartitioning(
                field="created_at",
                start=f"{anchor} - {total_days} DAYS",
                end=anchor,
                interval=interval_str,
            )

            exprs = partitioning.generate_expressions()

            # Expected partition count = ceil(total / interval)
            expected_count = math.ceil(total_days / interval_days)
            assert len(exprs) == expected_count, _compile(
                exprs[0]
            )  # show sample on fail

            # Basic sanity on first / last expression compilation
            compiled_first = _compile(exprs[0])
            compiled_last = _compile(exprs[-1])

            assert "created_at" in compiled_first
            assert "created_at" in compiled_last

            # First expression should start with an inclusive ">=" clause
            assert ">=" in compiled_first.split("AND")[0]

            # Last expression should end with the dynamic anchor
            expected_anchor_sql = "CURRENT_TIMESTAMP" if use_now else "CURRENT_DATE"
            assert compiled_last.endswith(expected_anchor_sql)


class TestRandomLiteralDayIntervals:
    """Random date literal ranges with DAY intervals."""

    RANDOM_SEED = 20240203

    @pytest.mark.parametrize("iterations", [20])
    def test_random_literal_date_ranges(self, iterations):  # type: ignore[override]
        random.seed(self.RANDOM_SEED)

        for _ in range(iterations):
            # Pick a random start date between 2020-01-01 and 2024-01-01
            year = random.randint(2020, 2023)
            month = random.randint(1, 12)
            day = random.randint(1, 28)  # keep it simple – avoid month length issues
            start_dt = datetime(year, month, day)

            # Random duration 1-60 days
            total_days = random.randint(1, 60)
            end_dt = start_dt + timedelta(days=total_days)

            # Random interval value (1-14 days) <= total_days
            interval_days = random.randint(1, min(14, total_days))
            interval_str = f"{interval_days} days"

            partitioning = TimeBasedPartitioning(
                field="event_date",
                start=start_dt.strftime("%Y-%m-%d"),
                end=end_dt.strftime("%Y-%m-%d"),
                interval=interval_str,
            )

            exprs = partitioning.generate_expressions()

            expected_count = math.ceil(total_days / interval_days)
            assert len(exprs) == expected_count

            # Compiled expressions should reference the DATE() literal
            compiled_any = _compile(random.choice(exprs))
            assert "DATE('" in compiled_any


class TestRandomMonthYearLiteralIntervals:
    """Randomised literal ranges with MONTH/YEAR intervals to exercise calendar logic."""

    RANDOM_SEED = 20240204

    @pytest.mark.parametrize("iterations", [15])
    def test_random_month_year_partitions(self, iterations):  # type: ignore[override]
        random.seed(self.RANDOM_SEED)

        for _ in range(iterations):
            # Choose unit (month / year)
            use_month = random.choice([True, False])
            interval_unit = "month" if use_month else "year"

            # Interval value (1-3 for months, 1-2 for years) – keeps test sizes reasonable
            interval_value = random.randint(1, 3) if use_month else random.randint(1, 2)
            interval_str = (
                f"{interval_value} {interval_unit}{'' if interval_value == 1 else 's'}"
            )

            # Pick a start date on the 1st of some month between 2018-01-01 and 2022-01-01
            year = random.randint(2018, 2021)
            month = random.randint(1, 12)
            start_dt = datetime(year, month, 1)

            # Random total units (e.g., 6-24 months or 2-5 years)
            total_units = random.randint(6, 24) if use_month else random.randint(2, 5)
            if use_month:
                # End date is start + N months – approximate by adding months in loop
                end_year = year + (month - 1 + total_units) // 12
                end_month = (month - 1 + total_units) % 12 + 1
                end_dt = datetime(end_year, end_month, 1)
            else:
                end_dt = datetime(year + total_units, month, 1)

            partitioning = TimeBasedPartitioning(
                field="created_at",
                start=start_dt.strftime("%Y-%m-%d"),
                end=end_dt.strftime("%Y-%m-%d"),
                interval=interval_str,
            )

            exprs = partitioning.generate_expressions()

            total_span_units = (
                _months_between(start_dt, end_dt)
                if use_month
                else (end_dt.year - start_dt.year)
            )
            expected_count = math.ceil(total_span_units / interval_value)
            assert len(exprs) == expected_count

            compiled_random = _compile(random.choice(exprs))
            # Ensure clause references the field and either an INTERVAL addition or a literal DATE boundary.
            assert "created_at" in compiled_random
