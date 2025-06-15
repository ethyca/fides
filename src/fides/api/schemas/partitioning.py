import re
from datetime import datetime, timedelta
from typing import List, Optional

from loguru import logger
from pydantic import Field, field_validator, model_validator
from sqlalchemy import and_, column, func, text
from sqlalchemy.sql import ColumnElement
from sqlalchemy_bigquery import BigQueryDialect

from fides.api.schemas.base_class import FidesSchema


class TimeBasedPartitioning(FidesSchema):
    """
    Generic time-based partitioning using pure SQLAlchemy constructs.
    Uses datetime.timedelta for all time calculations and SQLAlchemy expressions.
    """

    field: str = Field(description="Column name to partition on")
    start: Optional[str] = Field(default=None, description="Start time expression")
    end: Optional[str] = Field(default=None, description="End time expression")
    interval: Optional[str] = Field(
        default=None, description="Interval expression (e.g., '7 days', '2 weeks')"
    )

    @field_validator("start", "end")
    @classmethod
    def validate_time_expression(cls, v: str) -> str:
        """Validate time expressions."""
        if v is None:
            return v
        v = v.strip()
        patterns = [
            r"^now\(\)$",  # now()
            r"^today\(\)$",  # today()
            r"^now\(\)\s*[+-]\s*\d+\s+(day|days|week|weeks|month|months|year|years)$",  # now() +/- N unit
            r"^today\(\)\s*[+-]\s*\d+\s+(day|days|week|weeks|month|months|year|years)$",  # today() +/- N unit
            r"^\d{4}-\d{2}-\d{2}$",  # 2024-01-01
            r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$",  # 2024-01-01 12:00:00
        ]

        if not any(re.match(pattern, v, re.IGNORECASE) for pattern in patterns):
            raise ValueError(f"Unsupported time expression: {v}")
        return v.upper()  # Normalize to uppercase for consistency

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, v: str) -> str:
        """Validate interval expressions."""
        if v is None:
            return v
        v = v.strip().lower()
        if not re.match(r"^\d+\s+(day|days|week|weeks|month|months|year|years)$", v):
            raise ValueError(f"Invalid interval format: {v}")
        return v

    def _parse_interval(self) -> timedelta:
        """Parse interval string into timedelta."""
        if self.interval is None:
            # default to 0 days
            return timedelta(0)
        parts = str(self.interval).split()
        value = int(parts[0])
        unit = parts[1].lower()

        if unit in ["week", "weeks"]:
            return timedelta(weeks=value)
        if unit in ["day", "days"]:
            return timedelta(days=value)

        # For month/year we don't translate into timedelta (variable length)
        raise ValueError(
            "Month/Year intervals require special handling and are not returned as timedelta here."
        )

    def create_interval_text(self, time_delta: timedelta) -> str:
        """Create INTERVAL text expression from timedelta."""
        total_days = int(time_delta.total_seconds() / 86400)

        # Use weeks if it's a clean multiple of 7 days
        if total_days % 7 == 0 and total_days >= 7:
            return f"INTERVAL {total_days // 7} WEEK"
        return f"INTERVAL {total_days} DAY"

    def _parse_time_expression(self, expr: str) -> ColumnElement:
        """Convert time expression to SQLAlchemy expression."""
        expr = expr.strip().upper()

        if expr == "NOW()":
            return func.current_timestamp()

        # Handle TODAY() direct
        if expr == "TODAY()":
            return func.current_date()

        # Handle TODAY() arithmetic
        today_match = re.match(
            r"^TODAY\(\)\s*([+-])\s*(\d+)\s+(DAY|DAYS|WEEK|WEEKS|MONTH|MONTHS|YEAR|YEARS)$",
            expr,
        )

        if today_match:
            operator, value, unit = today_match.groups()
            unit = unit.upper()
            if unit in ["WEEK", "WEEKS"]:
                interval_text = f"INTERVAL {int(value)} WEEK"
            elif unit in ["DAY", "DAYS"]:
                interval_text = f"INTERVAL {int(value)} DAY"
            else:
                interval_text = f"INTERVAL {value} {unit.rstrip('S')}"

            base_expr = func.current_date()

            return (
                base_expr - text(interval_text)
                if operator == "-"
                else base_expr + text(interval_text)
            )

        # Handle NOW() arithmetic
        now_match = re.match(
            r"^NOW\(\)\s*([+-])\s*(\d+)\s+(DAY|DAYS|WEEK|WEEKS|MONTH|MONTHS|YEAR|YEARS)$",
            expr,
        )
        if now_match:
            operator, value, unit = now_match.groups()

            unit = unit.upper()
            if unit in ["WEEK", "WEEKS"]:
                time_delta = timedelta(weeks=int(value))
                interval_text = self.create_interval_text(time_delta)
            elif unit in ["DAY", "DAYS"]:
                time_delta = timedelta(days=int(value))
                interval_text = self.create_interval_text(time_delta)
            else:
                # MONTH/YEAR handled directly in SQL
                interval_text = f"INTERVAL {value} {unit.rstrip('S')}"

            base_expr = func.current_timestamp()

            return (
                base_expr - text(interval_text)
                if operator == "-"
                else base_expr + text(interval_text)
            )

        # Handle date literals
        if re.match(r"^\d{4}-\d{2}-\d{2}", expr):
            date_str = expr.split()[0]  # Remove time part if present
            return func.DATE(date_str)

        raise ValueError(f"Unsupported time expression: {expr}")

    def _calculate_total_duration(self) -> timedelta:
        """Calculate total duration between start and end as timedelta."""
        # Handle NOW()/TODAY() - X to NOW()/TODAY() pattern (days/weeks only)
        start_match = re.match(
            r"^NOW\(\)\s*-\s*(\d+)\s+(DAY|DAYS|WEEK|WEEKS)$", self.start
        )
        if start_match and str(self.end).upper() == "NOW()":
            value, unit = start_match.groups()
            return (
                timedelta(weeks=int(value))
                if unit.upper() in ["WEEK", "WEEKS"]
                else timedelta(days=int(value))
            )

        # TODAY() variant
        start_match = re.match(
            r"^TODAY\(\)\s*-\s*(\d+)\s+(DAY|DAYS|WEEK|WEEKS)$", self.start
        )
        if start_match and str(self.end).upper() == "TODAY()":
            value, unit = start_match.groups()
            return (
                timedelta(weeks=int(value))
                if unit.upper() in ["WEEK", "WEEKS"]
                else timedelta(days=int(value))
            )

        # Handle date literal ranges
        start_match = re.match(r"^(\d{4}-\d{2}-\d{2})", self.start)
        end_match = re.match(r"^(\d{4}-\d{2}-\d{2})", self.end)

        if start_match and end_match:
            start_date = datetime.strptime(start_match.group(1), "%Y-%m-%d")
            end_date = datetime.strptime(end_match.group(1), "%Y-%m-%d")

            if end_date <= start_date:
                raise ValueError(
                    f"End date must be after start date: {self.start} to {self.end}"
                )

            return end_date - start_date

        raise ValueError(
            f"Cannot calculate intervals for start='{self.start}' end='{self.end}'"
        )

    def _generate_intervals(
        self,
        field_column: ColumnElement,
        interval_time_delta: timedelta,
        total_duration: timedelta,
    ) -> List[ColumnElement]:
        """Generate non-overlapping conditions for fixed-length (day/week) intervals."""

        exclusive_first = self.__dict__.get("_exclusive_first_start", False)

        def _range_condition(
            start_exp: ColumnElement, end_exp: ColumnElement, is_first: bool
        ) -> ColumnElement:
            """Return an AND clause with configurable start inclusivity."""
            op_inclusive = False if (is_first and exclusive_first) else is_first
            op = (
                column(self.field) >= start_exp
                if op_inclusive
                else column(self.field) > start_exp
            )
            return and_(op, column(self.field) <= end_exp)

        conditions: List[ColumnElement] = []

        # Check if we're working with NOW() expressions (rolling window)
        is_now_based = (
            "NOW()" in str(self.start).upper() or "NOW()" in str(self.end).upper()
        )

        if is_now_based:
            current_offset = total_duration
            end_expr = self._parse_time_expression(self.end)
            first_interval = True

            while current_offset.total_seconds() > 0:
                start_offset = current_offset
                end_offset = current_offset - interval_time_delta
                if end_offset.total_seconds() < 0:
                    end_offset = timedelta(0)

                interval_start = (
                    func.current_timestamp()
                    if start_offset.total_seconds() == 0
                    else func.current_timestamp()
                    - text(self.create_interval_text(start_offset))
                )

                interval_end = (
                    end_expr
                    if end_offset.total_seconds() == 0
                    else func.current_timestamp()
                    - text(self.create_interval_text(end_offset))
                )

                conditions.append(
                    _range_condition(interval_start, interval_end, first_interval)
                )
                first_interval = False
                current_offset = end_offset
        else:
            start_expr = self._parse_time_expression(self.start)
            end_expr = self._parse_time_expression(self.end)
            current_offset = timedelta(0)
            first_interval = True

            # Detect TODAY() - N pattern for simplification
            today_match = re.match(
                r"^TODAY\(\)\s*-\s*(\d+)\s+(DAY|DAYS|WEEK|WEEKS)$",
                str(self.start).upper(),
            )
            simplify_today = today_match is not None
            if simplify_today:
                base_days = int(today_match.group(1)) * (
                    7 if today_match.group(2) in ["WEEK", "WEEKS"] else 1
                )

            while current_offset < total_duration:
                if simplify_today:
                    # compute offsets in days
                    offset_days = int(current_offset.total_seconds() / 86400)
                    start_days = base_days - offset_days

                    next_offset = current_offset + interval_time_delta
                    next_offset_days = int(next_offset.total_seconds() / 86400)
                    end_days = base_days - next_offset_days

                    interval_start = func.current_date() - text(
                        f"INTERVAL {start_days} DAY"
                    )
                    interval_end = (
                        end_expr
                        if next_offset >= total_duration
                        else func.current_date() - text(f"INTERVAL {end_days} DAY")
                    )
                else:
                    interval_start = (
                        start_expr
                        if current_offset.total_seconds() == 0
                        else start_expr
                        + text(self.create_interval_text(current_offset))
                    )

                    next_offset = current_offset + interval_time_delta
                    interval_end = (
                        end_expr
                        if next_offset >= total_duration
                        else start_expr + text(self.create_interval_text(next_offset))
                    )

                conditions.append(
                    _range_condition(interval_start, interval_end, first_interval)
                )
                first_interval = False
                current_offset = next_offset

        return conditions

    def generate_expressions(self) -> List[ColumnElement]:
        """Generate SQLAlchemy WHERE conditions for time-based or open-ended partitioning."""
        field_column: ColumnElement = column(self.field)

        # Open-ended scenarios
        if self.start is None and self.end is not None:
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
            raise ValueError(
                "An interval must be provided when both start and end are specified."
            )

        # Handle month/year intervals separately
        parts = self.interval.split()
        ivalue = int(parts[0])
        interval_unit = parts[1].lower()

        if interval_unit in ["month", "months", "year", "years"]:
            # Handle NOW() dynamic bounds
            if (
                re.match(
                    r"^NOW\(\)\s*-\s*\d+\s+(MONTH|MONTHS|YEAR|YEARS)$",
                    str(self.start).upper(),
                )
                and str(self.end).upper() == "NOW()"
            ):
                dyn_exprs = self._generate_dynamic_month_year(
                    field_column, ivalue, interval_unit
                )
                if dyn_exprs is not None:
                    return dyn_exprs
            return self._generate_month_year_intervals(
                field_column, ivalue, interval_unit
            )

        # day/week path (original)
        interval_time_delta = self._parse_interval()
        total_duration = self._calculate_total_duration()

        return self._generate_intervals(
            field_column, interval_time_delta, total_duration
        )

    def generate_where_clauses(self) -> List[str]:
        """Generate SQLAlchemy WHERE conditions for time-based partitioning."""
        raise NotImplementedError("generate_where_clauses not implemented")

    @model_validator(mode="after")
    def _validate_bounds_and_interval(self):
        """Ensure an interval is supplied when both start and end are provided."""
        if self.start is not None and self.end is not None and self.interval is None:
            raise ValueError(
                "An interval must be provided when both start and end are specified."
            )
        return self

    def _generate_month_year_intervals(
        self,
        field_column: ColumnElement,
        value: int,
        unit: str,
    ) -> List[ColumnElement]:
        """Generate interval conditions for month/year units where start & end are literals."""

        if not (_is_date_literal(self.start) and _is_date_literal(self.end)):
            # Fallback to single clause; complex dynamic expressions not supported yet.
            start_expr = (
                None if self.start is None else self._parse_time_expression(self.start)
            )
            end_expr = (
                None if self.end is None else self._parse_time_expression(self.end)
            )

            if start_expr is not None and end_expr is not None:
                return [and_(field_column >= start_expr, field_column <= end_expr)]
            if start_expr is not None:
                return [field_column >= start_expr]
            if end_expr is not None:
                return [field_column <= end_expr]

        # Both start/end are literals – rely on SQL to handle calendar nuances
        start_date = _date_value(self.start)
        end_date = _date_value(self.end)

        total_units = (
            (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            if unit.startswith("month")
            else end_date.year - start_date.year
        )

        # If the end day is greater than start day, ensure we include the partial unit
        if unit.startswith("month") and end_date.day > start_date.day:
            total_units += 1

        iterations = (total_units + value - 1) // value  # ceil division

        base_expr = func.DATE(start_date.strftime("%Y-%m-%d"))

        def offset_expr(multiplier: int):
            if multiplier == 0:
                return base_expr
            offset = multiplier * value
            return base_expr + text(f"INTERVAL {offset} {unit.rstrip('s').upper()}")

        conditions: List[ColumnElement] = []
        exclusive_first = self.__dict__.get("_exclusive_first_start", False)
        inclusive_start = not exclusive_first
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

    def _generate_dynamic_month_year(
        self, field_column: ColumnElement, value: int, unit: str
    ):
        """Generate slices for ranges like NOW() - N MONTHS .. NOW()"""
        start_match = re.match(
            r"^NOW\(\)\s*-\s*(\d+)\s+(MONTH|MONTHS|YEAR|YEARS)$",
            str(self.start).upper(),
        )
        if not start_match:
            return None
        total_units = int(start_match.group(1))

        if total_units % value != 0:
            return None  # cannot evenly divide, fallback to single clause

        iterations = total_units // value
        conditions: List[ColumnElement] = []
        inclusive_start = not self.__dict__.get("_exclusive_first_start", False)

        for i in range(iterations):
            start_offset_units = total_units - (i * value)
            end_offset_units = start_offset_units - value

            start_expr = func.current_timestamp() - text(
                f"INTERVAL {start_offset_units} {unit.rstrip('s').upper()}"
            )
            end_expr = (
                func.current_timestamp()
                if end_offset_units == 0
                else func.current_timestamp()
                - text(f"INTERVAL {end_offset_units} {unit.rstrip('s').upper()}")
            )

            start_op = (
                field_column >= start_expr
                if inclusive_start
                else field_column > start_expr
            )
            conditions.append(and_(start_op, field_column <= end_expr))
            inclusive_start = False

        return conditions


class BigQueryTimeBasedPartitioning(TimeBasedPartitioning):
    """Generates BigQuery-specific WHERE clauses for time-based partitioning."""

    def generate_where_clauses(self) -> List[str]:
        """Generate BigQuery-specific WHERE clauses."""
        conditions = self.generate_expressions()
        bigquery_dialect = BigQueryDialect()

        partition_clauses = []
        for condition in conditions:
            try:
                clause_str = str(
                    condition.compile(
                        dialect=bigquery_dialect,
                        compile_kwargs={"literal_binds": True},
                    )
                )
                partition_clauses.append(clause_str)
            except Exception as exc:
                logger.error("Could not generate where clause", exc_info=True)
                raise exc

        return partition_clauses


def _is_date_literal(expr: Optional[str]) -> bool:
    """Return True if the expression is a simple YYYY-MM-DD literal."""
    if expr is None:
        return False
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", expr.strip()))


def _date_value(expr: str) -> datetime:
    """Convert a YYYY-MM-DD literal into a datetime object (at midnight)."""
    return datetime.strptime(expr.strip(), "%Y-%m-%d")


def validate_partitioning_list(partitionings: List["TimeBasedPartitioning"]) -> None:
    """Validate that multiple TimeBasedPartitioning objects do not define overlapping
    ranges (inclusive).  Only specs whose *provided* bounds are literal YYYY-MM-DD
    strings participate in validation; any bound that is None is treated as
    open-ended (−∞ for ``start`` or +∞ for ``end``).  Specs with dynamic
    expressions like ``NOW()`` are skipped because we cannot resolve them at
    validation time.
    """

    def _materialize(p: "TimeBasedPartitioning"):
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
            if start_dt < previous_end:
                raise ValueError(
                    "Partitioning specifications overlap: '{}' - '{}' overlaps with a previous range.".format(
                        spec.start or "-infinity", spec.end or "+infinity"
                    )
                )
            if start_dt == previous_end:
                # Adjacent boundaries – mark second spec as exclusive on its first slice
                setattr(spec, "_exclusive_first_start", True)

        previous_end = end_dt

    return None
