# pylint: disable=too-many-branches, too-many-statements, too-many-return-statements, too-many-lines
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Set, Tuple

from pydantic import Field, field_validator, model_validator
from pydantic.json_schema import SkipJsonSchema
from sqlalchemy import and_, column, func, text
from sqlalchemy.sql import ColumnElement

from fides.api.schemas.base_class import FidesSchema

# ------------------------------------------------------------------
# Regular expression patterns reused across validation helpers.
# ------------------------------------------------------------------

NOW_LITERAL_REGEX = r"^NOW\(\)$"
TODAY_LITERAL_REGEX = r"^TODAY\(\)$"
TIMESTAMP_TODAY_LITERAL_REGEX = r"^TIMESTAMP\(TODAY\(\)\)$"

# Arithmetic offset pattern, e.g. "NOW() - 30 DAYS" or "TODAY() + 2 WEEKS"
ARITHMETIC_OFFSET_REGEX = (
    r"^(NOW|TODAY)\(\)\s*([+-])\s*(\d+)\s+"
    r"(DAY|DAYS|WEEK|WEEKS|MONTH|MONTHS|YEAR|YEARS)$"
)

# TIMESTAMP function with TODAY() and optional offset, e.g. "TIMESTAMP(TODAY() - 30 DAYS)"
TIMESTAMP_TODAY_OFFSET_REGEX = (
    r"^TIMESTAMP\(TODAY\(\)\s*([+-])\s*(\d+)\s+"
    r"(DAY|DAYS|WEEK|WEEKS|MONTH|MONTHS|YEAR|YEARS)\)$"
)

# Simple date & datetime literals
DATE_LITERAL_REGEX = r"^\d{4}-\d{2}-\d{2}$"
DATETIME_LITERAL_REGEX = r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$"
TIMESTAMP_DATE_LITERAL_REGEX = r"^TIMESTAMP\('\d{4}-\d{2}-\d{2}'\)$"
TIMESTAMP_DATETIME_LITERAL_REGEX = (
    r"^TIMESTAMP\('\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'\)$"
)

# Interval pattern (non-capturing) e.g. "7 DAYS", "2 WEEKS"
INTERVAL_REGEX = r"^\d+\s+(DAY|DAYS|WEEK|WEEKS|MONTH|MONTHS|YEAR|YEARS)$"
# Same pattern but with capturing groups for value & unit so we can parse quickly
INTERVAL_CAPTURE_REGEX = r"^(\d+)\s+(DAY|DAYS|WEEK|WEEKS|MONTH|MONTHS|YEAR|YEARS)$"

# Offset pattern for day/week units, captures NOW() or TODAY(), numeric value, and unit
DAY_WEEK_OFFSET_REGEX = r"^(NOW\(\)|TODAY\(\))\s*-\s*(\d+)\s+(DAY|DAYS|WEEK|WEEKS)$"

# Offset pattern for month/year units (captures base, numeric value, and unit)
MONTH_YEAR_OFFSET_REGEX = (
    r"^(NOW\(\)|TODAY\(\))\s*-\s*(\d+)\s+(MONTH|MONTHS|YEAR|YEARS)$"
)

# TIMESTAMP-wrapped offset patterns for day/week units
TIMESTAMP_DAY_WEEK_OFFSET_REGEX = (
    r"^TIMESTAMP\(TODAY\(\)\s*-\s*(\d+)\s+(DAY|DAYS|WEEK|WEEKS)\)$"
)

# TIMESTAMP-wrapped offset patterns for month/year units
TIMESTAMP_MONTH_YEAR_OFFSET_REGEX = (
    r"^TIMESTAMP\(TODAY\(\)\s*-\s*(\d+)\s+(MONTH|MONTHS|YEAR|YEARS)\)$"
)


class TimeUnit(str, Enum):
    """Standardized time units for partitioning."""

    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"

    @classmethod
    def parse(cls, raw: str) -> "TimeUnit":
        """Parse raw (possibly lowercase or plural) into a TimeUnit."""

        cleaned = raw.strip().upper().rstrip("S")
        try:
            return cls[cleaned]
        except KeyError as exc:
            raise ValueError(f"Unsupported time unit: {raw}") from exc


class TimeBasedPartitioning(FidesSchema):
    """
    Allows you to partition data based on time ranges using various
    time expressions and intervals.
    """

    # Generic time-based partitioning using pure SQLAlchemy constructs.
    # Uses datetime.timedelta for all time calculations and SQLAlchemy expressions.

    field: str = Field(
        description="Column name to partition on (e.g., `created_at`, `updated_at`)",
    )

    start: Optional[str] = Field(
        default=None,
        description="Start time expression. Supported formats: `NOW()`, `TODAY()`, `TIMESTAMP(TODAY())`, `YYYY-MM-DD`, `YYYY-MM-DD HH:MM:SS`, or arithmetic expressions like `NOW() - 30 DAYS`, `TIMESTAMP(TODAY() - 30 DAYS)`.",
    )

    end: Optional[str] = Field(
        default=None,
        description="End time expression. Same formats as start field.",
    )

    interval: Optional[str] = Field(
        description="Interval expression defining the size of each partition in `DAY(S)`, `WEEK(S)`, `MONTH(S)`, or `YEAR(S)`.",
        default=None,
    )

    # Determines whether the *first* slice produced by this partition spec
    # includes the lower bound (>=) or is exclusive (>).  Default is inclusive
    # and the value is *not* part of the public schema – it is manipulated by
    # helper utilities when combining multiple adjacent partitions.
    inclusive_start: SkipJsonSchema[bool] = Field(default=True, repr=False)

    # Example of using model_config with json_schema_extra for schema-level examples
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "field": "created_at",
                    "start": "NOW() - 30 DAYS",
                    "end": "NOW()",
                    "interval": "7 DAYS",
                },
                {
                    "field": "order_date",
                    "start": "2024-01-01",
                    "end": "2024-12-31",
                    "interval": "1 MONTH",
                },
                {
                    "field": "event_timestamp",
                    "start": "TODAY() - 1 YEAR",
                    "interval": "1 WEEK",
                },
                {
                    "field": "created_at",
                    "start": "TIMESTAMP(TODAY() - 7 DAYS)",
                    "end": "TIMESTAMP(TODAY())",
                    "interval": "1 DAY",
                },
            ]
        }
    }

    # ---------------------------------------------------------------------
    # Validators
    # ---------------------------------------------------------------------

    @field_validator("start", "end")
    @classmethod
    def validate_time_expression(cls, value: Optional[str]) -> Optional[str]:
        """Validate time expressions."""
        if value is None:
            return value
        v = value.strip().upper()
        patterns = [
            NOW_LITERAL_REGEX,
            TODAY_LITERAL_REGEX,
            TIMESTAMP_TODAY_LITERAL_REGEX,
            ARITHMETIC_OFFSET_REGEX,
            TIMESTAMP_TODAY_OFFSET_REGEX,
            DATE_LITERAL_REGEX,
            DATETIME_LITERAL_REGEX,
            TIMESTAMP_DATE_LITERAL_REGEX,
            TIMESTAMP_DATETIME_LITERAL_REGEX,
        ]

        if not any(re.match(pattern, v) for pattern in patterns):
            raise ValueError(f"Unsupported time expression: {v}")
        return v

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, value: Optional[str]) -> Optional[str]:
        """Validate interval expressions."""

        if value is None:
            return value
        v = value.strip().upper()
        if not re.match(INTERVAL_REGEX, v):
            raise ValueError(f"Invalid interval format: {v}")

        # Store normalized uppercase interval
        return v

    @model_validator(mode="after")
    def validate_bounds_and_interval(self) -> "TimeBasedPartitioning":
        """Ensure at least one bound is provided."""
        # At least one bound must be supplied.
        if self.start is None and self.end is None:
            raise ValueError("At least one of 'start' or 'end' must be provided.")

        return self

    # ---------------------------------------------------------------------
    # Interval helpers
    # ---------------------------------------------------------------------

    def _split_interval(self) -> Tuple[int, TimeUnit]:
        """Convert an interval string into a value and unit pair."""

        if self.interval is None:
            raise ValueError("Interval must be specified before it can be parsed.")

        normalized = str(self.interval).strip().upper()
        match = re.match(INTERVAL_CAPTURE_REGEX, normalized)
        if not match:
            raise ValueError(f"Invalid interval format: {self.interval}")

        value = int(match.group(1))
        unit = TimeUnit.parse(match.group(2))
        return value, unit

    def _timedelta_from_value_unit(self, value: int, unit: TimeUnit) -> timedelta:
        """Translate value/unit pairs into a `timedelta`."""

        if unit is TimeUnit.WEEK:
            return timedelta(weeks=value)
        if unit is TimeUnit.DAY:
            return timedelta(days=value)

        raise ValueError(
            "Only 'day' and 'week' units can be converted to timedelta – "
            f"received '{unit}'."
        )

    def _timedelta_to_interval(self, time_delta: timedelta) -> str:
        """Return a SQL `INTERVAL` clause for the supplied `timedelta`."""
        total_days = int(time_delta.total_seconds() / 86400)  # 86400 seconds in a day

        # Keep it in weeks if the interval is in weeks
        if self.interval and "WEEK" in self.interval:
            if total_days % 7 == 0 and total_days >= 7:
                return self.format_interval(total_days // 7, TimeUnit.WEEK)

        return self.format_interval(total_days, TimeUnit.DAY)

    def _parse_time_expression(self, expr: str) -> ColumnElement:
        """Convert time expression to SQLAlchemy expression."""
        expr = expr.strip().upper()

        if expr == "NOW()":
            return func.current_timestamp()

        # Handle TODAY() direct
        if expr == "TODAY()":
            return func.current_date()

        # Handle TIMESTAMP(TODAY()) - Today at 00:00:00 as timestamp
        if expr == "TIMESTAMP(TODAY())":
            return func.timestamp(func.current_date())

        # Handle TIMESTAMP(TODAY() - N UNIT) patterns
        timestamp_offset_match = re.match(TIMESTAMP_TODAY_OFFSET_REGEX, expr)
        if timestamp_offset_match:
            operator, value_str, unit_raw = timestamp_offset_match.groups()
            value = int(value_str)
            unit_raw = unit_raw.upper()

            # Build the TODAY() - N UNIT expression inside TIMESTAMP()
            base_date = func.current_date()

            # Build INTERVAL text
            if TimeUnit.parse(unit_raw) == TimeUnit.WEEK:
                interval_text = self._timedelta_to_interval(timedelta(weeks=value))
            elif TimeUnit.parse(unit_raw) == TimeUnit.DAY:
                interval_text = self._timedelta_to_interval(timedelta(days=value))
            else:  # MONTH / YEAR
                interval_text = self.format_interval(value, TimeUnit.parse(unit_raw))

            delta_expr = text(interval_text)

            # Apply offset to base date, then convert to timestamp
            date_with_offset = (
                base_date - delta_expr if operator == "-" else base_date + delta_expr
            )
            return func.timestamp(date_with_offset)

        # Handle arithmetic on NOW() and TODAY() via a single pattern
        arithmetic_match = re.match(ARITHMETIC_OFFSET_REGEX, expr)

        if arithmetic_match:
            func_name, operator, value_str, unit_raw = arithmetic_match.groups()

            value = int(value_str)
            unit_raw = unit_raw.upper()

            # Resolve base expression for NOW() vs TODAY()
            base_expr = (
                func.current_timestamp() if func_name == "NOW" else func.current_date()
            )

            # Build INTERVAL text
            if TimeUnit.parse(unit_raw) == TimeUnit.WEEK:
                interval_text = self._timedelta_to_interval(timedelta(weeks=value))
            elif TimeUnit.parse(unit_raw) == TimeUnit.DAY:
                interval_text = self._timedelta_to_interval(timedelta(days=value))
            else:  # MONTH / YEAR
                interval_text = self.format_interval(value, TimeUnit.parse(unit_raw))

            delta_expr = text(interval_text)

            return base_expr - delta_expr if operator == "-" else base_expr + delta_expr

        # Handle date literals
        if re.match(DATE_LITERAL_REGEX, expr):
            date_str = expr.split()[0]  # Remove time part if present
            return func.DATE(date_str)

        # Handle datetime literals
        if re.match(DATETIME_LITERAL_REGEX, expr):
            # Use TIMESTAMP function to convert string to timestamp for compatibility with interval arithmetic
            return func.timestamp(text(f"'{expr}'"))

        # Handle TIMESTAMP('date') literals
        if re.match(TIMESTAMP_DATE_LITERAL_REGEX, expr):
            # Extract the date from TIMESTAMP('2020-01-01') format
            date_match = re.search(r"'(\d{4}-\d{2}-\d{2})'", expr)
            if date_match:
                date_str = date_match.group(1)
                return func.timestamp(func.date(date_str))

        # Handle TIMESTAMP('datetime') literals
        if re.match(TIMESTAMP_DATETIME_LITERAL_REGEX, expr):
            # Extract the datetime from TIMESTAMP('2020-01-01 12:30:45') format
            datetime_match = re.search(
                r"'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'", expr
            )
            if datetime_match:
                datetime_str = datetime_match.group(1)
                return func.timestamp(text(f"'{datetime_str}'"))

        raise ValueError(f"Unsupported time expression: {expr}")

    def _calculate_total_duration(self) -> timedelta:
        """Calculate total duration between start and end as timedelta.

        Supported patterns
        ------------------
        1. `NOW() - N DAY|DAYS|WEEK|WEEKS to NOW()`
        2. `TODAY() - N DAY|DAYS|WEEK|WEEKS to TODAY()`
        3. `TIMESTAMP(TODAY() - N DAY|DAYS|WEEK|WEEKS) to TIMESTAMP(TODAY())`
        4. Both `start` and `end` are literal `YYYY-MM-DD` strings.
        """
        start_str = self.start or ""
        end_str = self.end or ""

        # Dynamic offsets expressed relative to NOW() or TODAY()
        start_offset_match = re.match(DAY_WEEK_OFFSET_REGEX, start_str)
        end_offset_match = re.match(DAY_WEEK_OFFSET_REGEX, end_str)

        # Additional pattern for MONTH/YEAR offsets so day/week interval slices can still be generated
        start_monthyear_match = re.match(MONTH_YEAR_OFFSET_REGEX, start_str)
        end_monthyear_match = re.match(MONTH_YEAR_OFFSET_REGEX, end_str)

        # TIMESTAMP-wrapped offset patterns
        start_timestamp_day_week_match = re.match(
            TIMESTAMP_DAY_WEEK_OFFSET_REGEX, start_str
        )
        end_timestamp_day_week_match = re.match(
            TIMESTAMP_DAY_WEEK_OFFSET_REGEX, end_str
        )
        start_timestamp_month_year_match = re.match(
            TIMESTAMP_MONTH_YEAR_OFFSET_REGEX, start_str
        )
        end_timestamp_month_year_match = re.match(
            TIMESTAMP_MONTH_YEAR_OFFSET_REGEX, end_str
        )

        # Case 1: start is offset, end is the base (NOW()/TODAY())
        if start_offset_match and end_str == start_offset_match.group(1):
            value = int(start_offset_match.group(2))
            unit = start_offset_match.group(3)

            return (
                timedelta(weeks=value)
                if unit in ["WEEK", "WEEKS"]
                else timedelta(days=value)
            )

        # Case 1b: TIMESTAMP patterns - start is TIMESTAMP(TODAY() - N UNIT), end is TIMESTAMP(TODAY())
        if start_timestamp_day_week_match and end_str == "TIMESTAMP(TODAY())":
            value = int(start_timestamp_day_week_match.group(1))
            unit = start_timestamp_day_week_match.group(2)

            return (
                timedelta(weeks=value)
                if unit in ["WEEK", "WEEKS"]
                else timedelta(days=value)
            )

        # Case 2: both start and end are offsets from the same base (NOW()/TODAY())
        # E.g. start = "NOW() - 1000 DAYS", end = "NOW() - 500 DAYS"
        if start_offset_match and end_offset_match:
            # Ensure both reference the same base function (NOW vs TODAY) and unit type
            if start_offset_match.group(1) == end_offset_match.group(
                1
            ) and start_offset_match.group(3) == end_offset_match.group(3):
                start_val = int(start_offset_match.group(2))
                end_val = int(end_offset_match.group(2))

                if start_val <= end_val:
                    raise ValueError(
                        "`start` offset must be greater (further in the past) than `end` offset"
                    )

                unit = start_offset_match.group(3)

                # The starting offset (start_val) represents the full duration back
                # from NOW()/TODAY(); we iterate from that point down toward the
                # end offset, generating slices sized by `interval`.  Therefore the
                # total duration for fixed-length slicing must be the *start* offset
                # – not the difference between start & end.

                total = start_val

                return (
                    timedelta(weeks=total)
                    if unit in ["WEEK", "WEEKS"]
                    else timedelta(days=total)
                )

        # Case 2b: both start and end are TIMESTAMP offsets
        # E.g. start = "TIMESTAMP(TODAY() - 14 DAYS)", end = "TIMESTAMP(TODAY() - 7 DAYS)"
        if start_timestamp_day_week_match and end_timestamp_day_week_match:
            start_val = int(start_timestamp_day_week_match.group(1))
            end_val = int(end_timestamp_day_week_match.group(1))
            start_unit = start_timestamp_day_week_match.group(2)
            end_unit = end_timestamp_day_week_match.group(2)

            # Ensure same unit type
            if start_unit == end_unit:
                if start_val <= end_val:
                    raise ValueError(
                        "`start` offset must be greater (further in the past) than `end` offset"
                    )

                # For backwards iteration from the dynamic base reference point (TODAY/NOW),
                # use the *start* offset as total duration so we iterate down toward the end bound
                total = start_val

                return (
                    timedelta(weeks=total)
                    if start_unit in ["WEEK", "WEEKS"]
                    else timedelta(days=total)
                )

        # Case 3: MONTH/YEAR offsets with DAY/WEEK interval requirements
        if start_monthyear_match:
            base_func = start_monthyear_match.group(1)
            start_val_raw = int(start_monthyear_match.group(2))
            start_unit_raw = start_monthyear_match.group(3)

            # Helper: convert raw month/year units into calendar months
            def _units_to_months(value: int, unit_raw: str) -> int:
                return value * (12 if unit_raw.startswith("YEAR") else 1)

            # If end is just the base (TODAY()/NOW())
            if end_str == base_func:
                total_months = _units_to_months(start_val_raw, start_unit_raw)
            # If end is another offset with same base
            elif end_monthyear_match and end_monthyear_match.group(1) == base_func:
                end_val_raw = int(end_monthyear_match.group(2))
                end_unit_raw = end_monthyear_match.group(3)

                start_months = _units_to_months(start_val_raw, start_unit_raw)
                end_months = _units_to_months(end_val_raw, end_unit_raw)

                if start_months <= end_months:
                    raise ValueError("`start` offset must be greater than `end` offset")

                # Use *start* offset as total duration so generator walks down toward end bound
                total_months = start_months
            else:
                total_months = None

            if total_months is not None:
                # Approximate months as 4 weeks each for timedelta purposes
                return timedelta(weeks=total_months * 4)

        # Case 3b: TIMESTAMP MONTH/YEAR offsets with DAY/WEEK interval requirements
        if start_timestamp_month_year_match:
            start_val_raw = int(start_timestamp_month_year_match.group(1))
            start_unit_raw = start_timestamp_month_year_match.group(2)

            # Helper: convert raw month/year units into calendar months
            def _units_to_months(value: int, unit_raw: str) -> int:
                return value * (12 if unit_raw.startswith("YEAR") else 1)

            # If end is TIMESTAMP(TODAY())
            if end_str == "TIMESTAMP(TODAY())":
                total_months = _units_to_months(start_val_raw, start_unit_raw)
            # If end is another TIMESTAMP offset
            elif end_timestamp_month_year_match:
                end_val_raw = int(end_timestamp_month_year_match.group(1))
                end_unit_raw = end_timestamp_month_year_match.group(2)

                start_months = _units_to_months(start_val_raw, start_unit_raw)
                end_months = _units_to_months(end_val_raw, end_unit_raw)

                if start_months <= end_months:
                    raise ValueError("`start` offset must be greater than `end` offset")

                # Use *start* offset as total duration
                total_months = start_months
            else:
                total_months = None

            if total_months is not None:
                # Approximate months as 4 weeks each for timedelta purposes
                return timedelta(weeks=total_months * 4)

        # Static literal YYYY-MM-DD date ranges or YYYY-MM-DD HH:MM:SS datetime ranges
        if _is_date_or_datetime_literal(start_str) and _is_date_or_datetime_literal(
            end_str
        ):
            start_date = _date_or_datetime_value(start_str)
            end_date = _date_or_datetime_value(end_str)

            if end_date <= start_date:
                raise ValueError(
                    f"End date must be after start date: {self.start} to {self.end}"
                )

            return end_date - start_date

        # Unsupported combination
        raise ValueError(
            f"Cannot calculate intervals for start='{self.start}' end='{self.end}'"
        )

    # ---------------------------------------------------------------------
    # Slice generators
    # ---------------------------------------------------------------------

    def _generate_fixed_length_slices(
        self,
        interval_time_delta: timedelta,
        total_duration: timedelta,
    ) -> List[ColumnElement]:
        """
        Generate non-overlapping conditions for fixed-length (day/week) intervals.
        """

        # First slice start is always inclusive (>=)
        def _range_condition(
            start_exp: ColumnElement, end_exp: ColumnElement, is_first: bool
        ) -> ColumnElement:
            """Return an AND clause with configurable start inclusivity."""
            op_inclusive = is_first
            op = (
                column(self.field) >= start_exp
                if op_inclusive
                else column(self.field) > start_exp
            )
            return and_(op, column(self.field) <= end_exp)

        conditions: List[ColumnElement] = []

        # Dynamic (NOW()/TODAY()) vs static ranges
        start_str = self.start or ""
        end_str = self.end or ""

        has_now = "NOW()" in start_str or "NOW()" in end_str
        has_today = "TODAY()" in start_str or "TODAY()" in end_str
        has_timestamp = "TIMESTAMP(" in start_str or "TIMESTAMP(" in end_str
        has_timestamp_literal = (
            _is_timestamp_date_literal(start_str)
            or _is_timestamp_date_literal(end_str)
            or _is_timestamp_datetime_literal(start_str)
            or _is_timestamp_datetime_literal(end_str)
        )

        if has_now or has_today:
            # Treat both NOW() and TODAY() as dynamic, using the appropriate base SQL
            base_expr = func.current_timestamp() if has_now else func.current_date()
            end_expr = self._parse_time_expression(end_str)

            # Helper function to apply timestamp wrapping when TIMESTAMP patterns are used
            def _maybe_wrap_timestamp(expr: ColumnElement) -> ColumnElement:
                if (
                    has_timestamp and not has_now and not has_timestamp_literal
                ):  # TIMESTAMP(TODAY()) patterns but not NOW() and not TIMESTAMP('date') literals
                    return func.timestamp(expr)
                return expr

            # Determine the relative offset (timedelta) that represents the user
            # supplied `end` bound so we do not generate slices beyond it.  If the
            # end expression is simply NOW()/TODAY(), the offset is zero.  If it
            # is an expression like "NOW() - 500 DAYS" we extract the numeric
            # offset so we can stop the fixed-length iteration once we reach it.

            end_offset_bound: timedelta = timedelta(0)

            dynamic_end_match = re.match(DAY_WEEK_OFFSET_REGEX, end_str)
            timestamp_end_match = re.match(TIMESTAMP_DAY_WEEK_OFFSET_REGEX, end_str)

            if dynamic_end_match is not None:
                numeric_val = int(dynamic_end_match.group(2))
                unit_raw = dynamic_end_match.group(3)
                end_offset_bound = (
                    timedelta(weeks=numeric_val)
                    if TimeUnit.parse(unit_raw) == TimeUnit.WEEK
                    else timedelta(days=numeric_val)
                )
            elif timestamp_end_match is not None:
                numeric_val = int(timestamp_end_match.group(1))
                unit_raw = timestamp_end_match.group(2)
                end_offset_bound = (
                    timedelta(weeks=numeric_val)
                    if TimeUnit.parse(unit_raw) == TimeUnit.WEEK
                    else timedelta(days=numeric_val)
                )

            # Extend dynamic_end_match for month/year offsets as weeks approximation
            if dynamic_end_match is None and timestamp_end_match is None:
                dynamic_end_match = re.match(MONTH_YEAR_OFFSET_REGEX, end_str)
                timestamp_end_match = re.match(
                    TIMESTAMP_MONTH_YEAR_OFFSET_REGEX, end_str
                )

            def _offset_to_timedelta(match_obj: Optional[re.Match]) -> timedelta:
                """Convert an offset regex match into a timedelta (weeks/days).

                For month/year units we approximate: month≈4 weeks, year≈52 weeks.
                """

                if match_obj is None:
                    return timedelta(0)

                numeric_val = int(match_obj.group(2))
                unit_raw = match_obj.group(3)

                unit_enum = TimeUnit.parse(unit_raw)

                if unit_enum is TimeUnit.WEEK:
                    return timedelta(weeks=numeric_val)
                if unit_enum is TimeUnit.DAY:
                    return timedelta(days=numeric_val)

                # Approximate month/year for slicing purposes
                if unit_enum is TimeUnit.MONTH:
                    return timedelta(weeks=numeric_val * 4)
                if unit_enum is TimeUnit.YEAR:
                    return timedelta(weeks=numeric_val * 52)

                return timedelta(0)

            def _timestamp_offset_to_timedelta(
                match_obj: Optional[re.Match],
            ) -> timedelta:
                """Convert a TIMESTAMP offset regex match into a timedelta (weeks/days).

                For month/year units we approximate: month≈4 weeks, year≈52 weeks.
                """

                if match_obj is None:
                    return timedelta(0)

                numeric_val = int(match_obj.group(1))
                unit_raw = match_obj.group(2)

                unit_enum = TimeUnit.parse(unit_raw)

                if unit_enum is TimeUnit.WEEK:
                    return timedelta(weeks=numeric_val)
                if unit_enum is TimeUnit.DAY:
                    return timedelta(days=numeric_val)

                # Approximate month/year for slicing purposes
                if unit_enum is TimeUnit.MONTH:
                    return timedelta(weeks=numeric_val * 4)
                if unit_enum is TimeUnit.YEAR:
                    return timedelta(weeks=numeric_val * 52)

                return timedelta(0)

            # Update end_offset_bound for month/year patterns if not already set
            if end_offset_bound == timedelta(0):
                if dynamic_end_match is not None:
                    end_offset_bound = _offset_to_timedelta(dynamic_end_match)
                elif timestamp_end_match is not None:
                    end_offset_bound = _timestamp_offset_to_timedelta(
                        timestamp_end_match
                    )

            # Iterate from the starting offset (total_duration) backward toward
            # the end offset, generating non-overlapping slices until just before
            # we would cross the end bound.

            current_offset = total_duration
            first_interval = self.inclusive_start

            while current_offset > end_offset_bound:
                start_offset = current_offset
                end_offset = current_offset - interval_time_delta

                # If subtracting the interval would step past the end bound,
                # clamp the end_offset to the bound so the final slice lands
                # exactly on the user-provided end expression.
                end_offset = max(end_offset, end_offset_bound)

                # Clamp negative end offsets to zero (aligns with base_expr)
                if end_offset.total_seconds() < 0:
                    end_offset = timedelta(0)

                # Build expressions first – needed for equality check
                interval_start = (
                    _maybe_wrap_timestamp(base_expr)
                    if start_offset.total_seconds() == 0
                    else _maybe_wrap_timestamp(
                        base_expr - text(self._timedelta_to_interval(start_offset))
                    )
                )

                interval_end = (
                    end_expr
                    if end_offset.total_seconds() == 0
                    else _maybe_wrap_timestamp(
                        base_expr - text(self._timedelta_to_interval(end_offset))
                    )
                )

                # Skip zero-length slice
                if str(interval_start) == str(interval_end):
                    break

                conditions.append(
                    _range_condition(interval_start, interval_end, first_interval)
                )
                first_interval = False
                current_offset = end_offset
        else:
            # Static literal or dynamic expressions already parsed – walk forward from start
            start_expr = self._parse_time_expression(start_str)
            end_expr = self._parse_time_expression(end_str)

            # Helper function to apply timestamp wrapping when TIMESTAMP patterns are used
            def _maybe_wrap_timestamp(expr: ColumnElement) -> ColumnElement:
                if (
                    has_timestamp and not has_now and not has_timestamp_literal
                ):  # TIMESTAMP(TODAY()) patterns but not NOW() and not TIMESTAMP('date') literals
                    return func.timestamp(expr)
                return expr

            current_offset = timedelta(0)
            first_interval = self.inclusive_start

            while current_offset < total_duration:
                interval_start = (
                    start_expr
                    if current_offset.total_seconds() == 0
                    else _maybe_wrap_timestamp(
                        start_expr + text(self._timedelta_to_interval(current_offset))
                    )
                )

                next_offset = current_offset + interval_time_delta
                interval_end = (
                    end_expr
                    if next_offset >= total_duration
                    else _maybe_wrap_timestamp(
                        start_expr + text(self._timedelta_to_interval(next_offset))
                    )
                )

                conditions.append(
                    _range_condition(interval_start, interval_end, first_interval)
                )
                first_interval = False
                current_offset = next_offset

        return conditions

    def _generate_calendar_slices(
        self,
        field_column: ColumnElement,
        value: int,
        unit: TimeUnit,
    ) -> List[ColumnElement]:
        """Generate interval conditions for month/year units where start & end are literals."""

        start_str = self.start or ""
        end_str = self.end or ""

        if not (_is_date_literal(start_str) and _is_date_literal(end_str)):
            # Fallback to single clause; complex dynamic expressions not supported yet.
            start_expr = (
                None if self.start is None else self._parse_time_expression(start_str)
            )
            end_expr = (
                None if self.end is None else self._parse_time_expression(end_str)
            )

            if start_expr is not None and end_expr is not None:
                return [and_(field_column >= start_expr, field_column <= end_expr)]
            if start_expr is not None:
                return [field_column >= start_expr]
            if end_expr is not None:
                return [field_column <= end_expr]

        # Both start/end are literals – rely on SQL to handle calendar nuances
        start_date = _date_value(start_str)
        end_date = _date_value(end_str)

        total_units = (
            (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            if unit is TimeUnit.MONTH
            else end_date.year - start_date.year
        )

        # If the end day is greater than start day, ensure we include the partial unit
        if unit is TimeUnit.MONTH and end_date.day > start_date.day:
            total_units += 1

        iterations = (total_units + value - 1) // value  # ceil division

        base_expr = func.DATE(start_date.strftime("%Y-%m-%d"))

        def offset_expr(multiplier: int) -> ColumnElement:
            if multiplier == 0:
                return base_expr
            offset = multiplier * value
            return base_expr + text(self.format_interval(offset, unit))

        conditions: List[ColumnElement] = []
        inclusive_start = self.inclusive_start  # Respect spec setting
        for i in range(iterations):
            start_exp = offset_expr(i)

            # Determine end expression for this slice
            next_multiplier = i + 1
            end_exp = (
                func.DATE(end_date.strftime("%Y-%m-%d"))
                if next_multiplier * value >= total_units
                else offset_expr(next_multiplier)
            )

            conditions.append(
                and_(
                    (
                        (field_column >= start_exp)
                        if inclusive_start
                        else (field_column > start_exp)
                    ),
                    field_column <= end_exp,
                )
            )
            inclusive_start = False

        return conditions

    def _generate_dynamic_month_year_slices(
        self,
        field_column: ColumnElement,
        value: int,
        unit: TimeUnit,
    ) -> Optional[List[ColumnElement]]:
        """Generate slices for dynamic ranges expressed in months or years.

        Supported patterns
        -----------------
        1. `NOW()   - N <unit>s TO NOW()`   (timestamp based)
        2. `TODAY() - N <unit>s TO TODAY()` (date based)
        3. `TIMESTAMP(TODAY() - N <unit>s) TO TIMESTAMP(TODAY())` (timestamp based)

        The helper chooses `CURRENT_TIMESTAMP` or `CURRENT_DATE` automatically
        based on which pattern is matched.
        """

        start_str = self.start or ""
        end_str = self.end or ""

        # --- START PATTERN MATCHES -------------------------------------------------
        # - Scenario A: start is offset, end is TODAY()/NOW()
        # - Scenario B: start and end are both offsets from the same base (NOW/TODAY)
        # - Scenario C: start is TIMESTAMP offset, end is TIMESTAMP(TODAY())
        # - Scenario D: start and end are both TIMESTAMP offsets

        start_match = re.match(MONTH_YEAR_OFFSET_REGEX, start_str)
        start_timestamp_match = re.match(TIMESTAMP_MONTH_YEAR_OFFSET_REGEX, start_str)

        if start_match is None and start_timestamp_match is None:
            return None

        end_match = re.match(MONTH_YEAR_OFFSET_REGEX, end_str)
        end_timestamp_match = re.match(TIMESTAMP_MONTH_YEAR_OFFSET_REGEX, end_str)

        # Determine which pattern we're using and extract values
        if start_match is not None:
            # Traditional NOW()/TODAY() pattern
            base_func_name = start_match.group(1)  # NOW or TODAY
            start_units_raw = int(start_match.group(2))
            start_unit_enum = TimeUnit.parse(start_match.group(3))
            use_current_date = base_func_name == "TODAY()"
            is_timestamp_pattern = False
        elif start_timestamp_match is not None:
            # TIMESTAMP pattern
            start_units_raw = int(start_timestamp_match.group(1))
            start_unit_enum = TimeUnit.parse(start_timestamp_match.group(2))
            use_current_date = True  # TIMESTAMP(TODAY()) uses CURRENT_DATE as base
            is_timestamp_pattern = True
        else:
            # This shouldn't happen due to the earlier check, but makes mypy happy
            return None

        # Helper to convert raw units (possibly years) into desired interval unit count
        def _convert_units(raw_units: int, raw_unit_enum: TimeUnit) -> Optional[int]:
            if raw_unit_enum is unit:
                return raw_units
            if raw_unit_enum is TimeUnit.YEAR and unit is TimeUnit.MONTH:
                return raw_units * 12
            return None  # unsupported mismatch

        conditions: List[ColumnElement] = []

        # Scenario A: `... TO NOW()/TODAY()` or `... TO TIMESTAMP(TODAY())`
        # Break down complex condition for pylint
        traditional_to_base = not is_timestamp_pattern and end_match is None
        traditional_to_zero_offset = (
            not is_timestamp_pattern
            and end_match is not None
            and end_match.group(1) == base_func_name
            and int(end_match.group(2)) == 0
        )
        timestamp_to_today = is_timestamp_pattern and end_str == "TIMESTAMP(TODAY())"

        if traditional_to_base or traditional_to_zero_offset or timestamp_to_today:
            total_units = _convert_units(start_units_raw, start_unit_enum)
            if total_units is None or total_units % value != 0:
                return None

            iterations = total_units // value
            inclusive_start = self.inclusive_start
            base_expr = (
                func.current_date() if use_current_date else func.current_timestamp()
            )

            for i in range(iterations):
                start_offset_units = total_units - (i * value)
                end_offset_units = start_offset_units - value

                start_expr = base_expr - text(
                    self.format_interval(start_offset_units, unit)
                )
                if end_offset_units == 0:
                    if is_timestamp_pattern:
                        end_expr = func.timestamp(base_expr)
                    else:
                        end_expr = base_expr
                else:
                    end_expr = base_expr - text(
                        self.format_interval(end_offset_units, unit)
                    )

                start_op = (
                    field_column >= start_expr
                    if inclusive_start
                    else field_column > start_expr
                )
                conditions.append(and_(start_op, field_column <= end_expr))
                inclusive_start = False

            return conditions

        # Scenario B: both start and end are offsets (traditional or TIMESTAMP)
        if (
            not is_timestamp_pattern
            and end_match is not None
            and end_match.group(1) == base_func_name
        ) or (is_timestamp_pattern and end_timestamp_match is not None):

            if is_timestamp_pattern and end_timestamp_match is not None:
                end_units_raw = int(end_timestamp_match.group(1))
                end_unit_enum = TimeUnit.parse(end_timestamp_match.group(2))
            elif end_match is not None:
                end_units_raw = int(end_match.group(2))
                end_unit_enum = TimeUnit.parse(end_match.group(3))
            else:
                # This shouldn't happen due to the earlier check, but makes mypy happy
                return None

            start_units_converted = _convert_units(start_units_raw, start_unit_enum)
            end_units_converted = _convert_units(end_units_raw, end_unit_enum)
            if (
                start_units_converted is None
                or end_units_converted is None
                or start_units_converted <= end_units_converted
            ):
                return None

            total_units = start_units_converted - end_units_converted
            if total_units % value != 0:
                return None

            iterations = total_units // value
            inclusive_start = self.inclusive_start
            base_expr = (
                func.current_date() if use_current_date else func.current_timestamp()
            )

            for i in range(iterations):
                slice_start_units = start_units_converted - (i * value)
                slice_end_units = slice_start_units - value

                start_expr = base_expr - text(
                    self.format_interval(slice_start_units, unit)
                )
                if is_timestamp_pattern:
                    end_expr = func.timestamp(
                        base_expr - text(self.format_interval(slice_end_units, unit))
                    )
                else:
                    end_expr = base_expr - text(
                        self.format_interval(slice_end_units, unit)
                    )

                start_op = (
                    field_column >= start_expr
                    if inclusive_start
                    else field_column > start_expr
                )
                conditions.append(and_(start_op, field_column <= end_expr))
                inclusive_start = False

            return conditions

        return None  # Fallback to other generation paths

    def _generate_literal_to_now_month_year_slices(
        self,
        field_column: ColumnElement,
        value: int,
        unit: TimeUnit,
    ) -> List[ColumnElement]:
        """Generate partitions when start is a YYYY-MM-DD literal and end
        is NOW() or TODAY() with month/year interval.

        The logic mirrors _generate_calendar_slices, but the end
        bound is dynamic so we calculate the number of complete units between
        start and the current date/time at runtime.
        """

        assert self.start is not None  # for mypy
        start_date = _date_value(self.start)

        # Choose appropriate SQL base expressions depending on TODAY/NOW/TIMESTAMP(TODAY())
        end_str = str(self.end)
        end_is_today = end_str == "TODAY()"
        end_is_timestamp_today = end_str == "TIMESTAMP(TODAY())"

        if end_is_timestamp_today:
            base_now_expr = func.timestamp(func.current_date())
        else:
            base_now_expr = (
                func.current_date() if end_is_today else func.current_timestamp()
            )

        # Calculate total units between start literal and "now"
        now_dt = datetime.utcnow()

        if unit is TimeUnit.MONTH:
            total_units = (now_dt.year - start_date.year) * 12 + (
                now_dt.month - start_date.month
            )
            if now_dt.day > start_date.day:
                total_units += 1
        else:  # TimeUnit.YEAR
            total_units = now_dt.year - start_date.year
            if (now_dt.month, now_dt.day) > (start_date.month, start_date.day):
                total_units += 1

        iterations = (total_units + value - 1) // value  # ceil division

        base_expr = func.DATE(start_date.strftime("%Y-%m-%d"))

        def offset_expr(multiplier: int) -> ColumnElement:
            if multiplier == 0:
                return base_expr
            offset = multiplier * value
            return base_expr + text(self.format_interval(offset, unit))

        conditions: List[ColumnElement] = []
        inclusive_start = self.inclusive_start  # First slice always inclusive

        for i in range(iterations):
            start_exp = offset_expr(i)

            next_mult = i + 1
            end_exp = (
                base_now_expr
                if next_mult * value >= total_units
                else offset_expr(next_mult)
            )

            start_op = (
                field_column >= start_exp
                if inclusive_start
                else field_column > start_exp
            )
            conditions.append(and_(start_op, field_column <= end_exp))
            inclusive_start = False

        return conditions

    # ---------------------------------------------------------------------
    # Public methods
    # ---------------------------------------------------------------------

    def format_interval(self, value: int, unit: TimeUnit) -> str:
        """Return a SQL snippet representing time interval.

        Default implementation emits the ANSI-ish style used by BigQuery and
        many other engines: `INTERVAL <N> DAY` or `INTERVAL <N> WEEK`.

        Subclasses may override if their dialect differs (e.g., Postgres prefers
        `INTERVAL '<N> day'`).
        """
        unit_str = unit.value
        return f"INTERVAL {value} {unit_str}"

    def generate_expressions(self) -> List[ColumnElement]:
        """
        Generate SQLAlchemy WHERE conditions for time-based or open-ended partitioning.
        This is the main entry point for the partition generation logic.
        """

        field_column: ColumnElement = column(self.field)

        # Open-ended scenarios
        if self.start is None and self.end is not None:
            assert self.end is not None  # for mypy
            end_expr = self._parse_time_expression(self.end)
            return [field_column <= end_expr]

        if self.end is None and self.start is not None:
            start_expr = self._parse_time_expression(self.start)
            return [field_column >= start_expr]

        if self.start is None or self.end is None:
            raise ValueError(
                "Either both start and end must be provided, or one open-bound with the other bound specified."
            )

        if self.interval is None:
            # No interval specified - return a single condition covering the entire range
            start_expr = self._parse_time_expression(self.start)
            end_expr = self._parse_time_expression(self.end)
            start_op = (
                field_column >= start_expr
                if self.inclusive_start
                else field_column > start_expr
            )
            return [and_(start_op, field_column <= end_expr)]

        # Determine interval value and unit (Enum)
        interval_value, interval_unit = self._split_interval()

        if interval_unit in (TimeUnit.MONTH, TimeUnit.YEAR):
            end_str = self.end or ""

            # Try dynamic slice generation for various NOW()/TODAY() offset scenarios.
            dynamic_expressions = self._generate_dynamic_month_year_slices(
                field_column, interval_value, interval_unit
            )
            if dynamic_expressions is not None:
                return dynamic_expressions

            # Literal start -> NOW()/TODAY()/TIMESTAMP(TODAY()) end
            if _is_date_literal(self.start) and end_str in (
                "NOW()",
                "TODAY()",
                "TIMESTAMP(TODAY())",
            ):
                return self._generate_literal_to_now_month_year_slices(
                    field_column, interval_value, interval_unit
                )

            # Fallback to calendar slicing when both bounds are literals
            return self._generate_calendar_slices(
                field_column, interval_value, interval_unit
            )

        # day/week (fixed length) path
        interval_time_delta = self._timedelta_from_value_unit(
            interval_value, interval_unit
        )
        total_duration = self._calculate_total_duration()

        return self._generate_fixed_length_slices(
            interval_time_delta,
            total_duration,
        )

    def generate_where_clauses(self) -> List[str]:
        """
        Generate SQLAlchemy WHERE conditions for time-based partitioning.
        This needs to be implemented by subclasses to generate the
        dialect-specific WHERE clauses.
        """

        raise NotImplementedError("generate_where_clauses not implemented")


def validate_partitioning_list(partitionings: List["TimeBasedPartitioning"]) -> None:
    """Validate that multiple TimeBasedPartitioning objects do not define overlapping
    ranges (inclusive) and that all partitioning objects use the same field name.
    Only specs whose provided bounds are literal YYYY-MM-DD strings participate in
    overlap validation; any bound that is None is treated as open-ended (-infinity
    for `start` or +infinity for `end`).  Specs with dynamic expressions like `NOW()`
    are skipped because we cannot resolve them at validation time.
    """

    # Validate that all partitions use the same field
    if len(partitionings) > 1:
        first_field = partitionings[0].field
        for i, partition in enumerate(partitionings[1:], 1):
            if partition.field != first_field:
                raise ValueError(
                    f"All partitioning specifications must use the same field. "
                    f"Expected '{first_field}' but found '{partition.field}' at index {i}."
                )

    def _materialize(
        p: "TimeBasedPartitioning",
    ) -> Optional[Tuple[datetime, datetime, "TimeBasedPartitioning"]]:
        if p.start is not None and not _is_date_literal(p.start):
            return None  # skip – dynamic expression
        if p.end is not None and not _is_date_literal(p.end):
            return None  # skip – dynamic expression

        start_dt = _date_value(p.start) if p.start is not None else datetime.min
        end_dt = _date_value(p.end) if p.end is not None else datetime.max
        return (start_dt, end_dt, p)

    materialized = [_materialize(p) for p in partitionings]
    comparable_specs = [m for m in materialized if m is not None]

    # Sort by start datetime so consecutive comparison works
    comparable_specs.sort(key=lambda tup: tup[0])

    previous_end: Optional[datetime] = None
    for start_dt, end_dt, spec in comparable_specs:
        if previous_end is not None:
            if start_dt <= previous_end:
                raise ValueError(
                    "Partitioning specifications overlap or touch: '{}' - '{}' overlaps with a previous range.".format(
                        spec.start or "-infinity", spec.end or "+infinity"
                    )
                )
        previous_end = end_dt


def _is_date_literal(expr: Optional[str]) -> bool:
    """Return True if the expression is a simple YYYY-MM-DD literal."""
    if expr is None:
        return False
    return bool(re.match(DATE_LITERAL_REGEX, expr.strip()))


def _is_datetime_literal(expr: Optional[str]) -> bool:
    """Return True if the expression is a YYYY-MM-DD HH:MM:SS literal."""
    if expr is None:
        return False
    return bool(re.match(DATETIME_LITERAL_REGEX, expr.strip()))


def _is_timestamp_date_literal(expr: Optional[str]) -> bool:
    """Return True if the expression is a TIMESTAMP('YYYY-MM-DD') literal."""
    if expr is None:
        return False
    return bool(re.match(TIMESTAMP_DATE_LITERAL_REGEX, expr.strip()))


def _is_timestamp_datetime_literal(expr: Optional[str]) -> bool:
    """Return True if the expression is a TIMESTAMP('YYYY-MM-DD HH:MM:SS') literal."""
    if expr is None:
        return False
    return bool(re.match(TIMESTAMP_DATETIME_LITERAL_REGEX, expr.strip()))


def _is_date_or_datetime_literal(expr: Optional[str]) -> bool:
    """Return True if the expression is either a date or datetime literal."""
    return (
        _is_date_literal(expr)
        or _is_datetime_literal(expr)
        or _is_timestamp_date_literal(expr)
        or _is_timestamp_datetime_literal(expr)
    )


def _date_value(expr: str) -> datetime:
    """Convert a YYYY-MM-DD literal into a datetime object (at midnight)."""
    return datetime.strptime(expr.strip(), "%Y-%m-%d")


def _datetime_value(expr: str) -> datetime:
    """Convert a YYYY-MM-DD HH:MM:SS literal into a datetime object."""
    return datetime.strptime(expr.strip(), "%Y-%m-%d %H:%M:%S")


def _timestamp_literal_value(expr: str) -> datetime:
    """Extract datetime from TIMESTAMP('date') or TIMESTAMP('datetime') literal."""
    if _is_timestamp_date_literal(expr):
        # Extract date from TIMESTAMP('2024-01-01') format
        date_match = re.search(r"'(\d{4}-\d{2}-\d{2})'", expr)
        if date_match:
            date_str = date_match.group(1)
            return datetime.strptime(date_str, "%Y-%m-%d")
    elif _is_timestamp_datetime_literal(expr):
        # Extract datetime from TIMESTAMP('2024-01-01 12:30:45') format
        datetime_match = re.search(r"'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'", expr)
        if datetime_match:
            datetime_str = datetime_match.group(1)
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

    raise ValueError(f"Invalid TIMESTAMP literal: {expr}")


def _date_or_datetime_value(expr: str) -> datetime:
    """Convert a date or datetime literal into a datetime object."""
    if _is_date_literal(expr):
        return _date_value(expr)
    if _is_datetime_literal(expr):
        return _datetime_value(expr)
    if _is_timestamp_date_literal(expr) or _is_timestamp_datetime_literal(expr):
        return _timestamp_literal_value(expr)
    raise ValueError(f"Expression is not a date or datetime literal: {expr}")


# Required external keys for a time-based partitioning spec.  Internal helper
# attributes like `inclusive_start` are intentionally excluded.
TIME_BASED_REQUIRED_KEYS: Set[str] = {"field", "start", "end", "interval"}

# ------------------------------------------------------------------
# Utilities for working with lists of partition specs
# ------------------------------------------------------------------


def combine_partitions(parts: List["TimeBasedPartitioning"]) -> List[ColumnElement]:
    """Return a combined list of SQLAlchemy expressions for an list
    of `TimeBasedPartitioning` objects, ensuring adjacent specs do not
    overlap at the boundary row.

    If two consecutive specs share a boundary (`prev.end == curr.start`) the
    current spec's first slice is made exclusive by toggling its internal
    `inclusive_start` flag.
    """

    combined: List[ColumnElement] = []

    validate_partitioning_list(parts)

    for idx, spec in enumerate(parts):
        p = spec.model_copy(deep=True)  # avoid mutating caller's object

        if idx > 0 and p.start is not None and parts[idx - 1].end is not None:
            if p.start == parts[idx - 1].end:
                p.inclusive_start = False

        combined.extend(p.generate_expressions())

    return combined


__all__ = [
    "TIME_BASED_REQUIRED_KEYS",
    "TimeBasedPartitioning",
    "combine_partitions",
    "validate_partitioning_list",
]
