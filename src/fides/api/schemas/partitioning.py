import re
from datetime import datetime, timedelta
from typing import List

from loguru import logger
from pydantic import Field, field_validator
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
    start: str = Field(description="Start time expression")
    end: str = Field(description="End time expression")
    interval: str = Field(description="Interval expression (e.g., '7 days', '2 weeks')")

    @field_validator("start", "end")
    @classmethod
    def validate_time_expression(cls, v: str) -> str:
        """Validate time expressions."""
        v = v.strip()
        patterns = [
            r"^now\(\)$",  # now()
            r"^now\(\)\s*[+-]\s*\d+\s+(day|days|week|weeks)$",  # now() +/- N unit
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
        v = v.strip().lower()
        if not re.match(r"^\d+\s+(day|days|week|weeks)$", v):
            raise ValueError(f"Invalid interval format: {v}")
        return v

    def _parse_interval(self) -> timedelta:
        """Parse interval string into timedelta."""
        parts = str(self.interval).split()
        value = int(parts[0])
        unit = parts[1]

        if unit in ["week", "weeks"]:
            return timedelta(weeks=value)
        return timedelta(days=value)

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

        # Handle NOW() arithmetic
        now_match = re.match(
            r"^NOW\(\)\s*([+-])\s*(\d+)\s+(DAY|DAYS|WEEK|WEEKS)$", expr
        )
        if now_match:
            operator, value, unit = now_match.groups()

            # Create timedelta
            time_delta = (
                timedelta(weeks=int(value))
                if unit in ["WEEK", "WEEKS"]
                else timedelta(days=int(value))
            )

            interval_text = self.create_interval_text(time_delta)
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
        # Handle NOW() - X to NOW() pattern
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
        """Generate interval conditions using clean INTERVAL text expressions."""
        conditions: List[ColumnElement] = []

        # Check if we're working with NOW() expressions
        is_now_based = (
            "NOW()" in str(self.start).upper() or "NOW()" in str(self.end).upper()
        )

        if is_now_based:
            # Handle NOW() - X to NOW() pattern (work backwards from furthest to most recent)
            current_offset = total_duration
            end_expr = self._parse_time_expression(self.end)

            while current_offset.total_seconds() > 0:
                start_offset = current_offset
                end_offset = current_offset - interval_time_delta
                if end_offset.total_seconds() < 0:
                    end_offset = timedelta(0)

                # Calculate interval start
                interval_start = (
                    func.current_timestamp()
                    if start_offset.total_seconds() == 0
                    else func.current_timestamp()
                    - text(self.create_interval_text(start_offset))
                )

                # Calculate interval end
                interval_end = (
                    end_expr
                    if end_offset.total_seconds() == 0
                    else func.current_timestamp()
                    - text(self.create_interval_text(end_offset))
                )

                conditions.append(
                    and_(field_column > interval_start, field_column <= interval_end)
                )
                current_offset = end_offset
        else:
            # Handle date literal ranges (work forwards from start to end)
            start_expr = self._parse_time_expression(self.start)
            end_expr = self._parse_time_expression(self.end)
            current_offset = timedelta(0)

            while current_offset < total_duration:
                # Calculate interval start
                interval_start = (
                    start_expr
                    if current_offset.total_seconds() == 0
                    else start_expr + text(self.create_interval_text(current_offset))
                )

                # Calculate interval end
                next_offset = current_offset + interval_time_delta
                interval_end = (
                    end_expr
                    if next_offset >= total_duration
                    else start_expr + text(self.create_interval_text(next_offset))
                )

                conditions.append(
                    and_(field_column > interval_start, field_column <= interval_end)
                )
                current_offset = next_offset

        return conditions

    def generate_expressions(self) -> List[ColumnElement]:
        """Generate SQLAlchemy WHERE conditions for time-based partitioning."""
        field_column: ColumnElement = column(self.field)
        interval_time_delta = self._parse_interval()
        total_duration = self._calculate_total_duration()

        return self._generate_intervals(
            field_column, interval_time_delta, total_duration
        )

    def generate_where_clauses(self) -> List[str]:
        """Generate SQLAlchemy WHERE conditions for time-based partitioning."""
        raise NotImplementedError("generate_where_clauses not implemented")


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
