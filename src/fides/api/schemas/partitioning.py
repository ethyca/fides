import re
from datetime import datetime, timedelta
from typing import List

from loguru import logger
from pydantic import Field, field_validator
from sqlalchemy import and_, column, func, text
from sqlalchemy.sql import ColumnElement
from sqlalchemy.sql.expression import BinaryExpression
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
        match = re.match(r"^(\d+)\s+(day|days|week|weeks)$", self.interval)
        if not match:
            raise ValueError(f"Invalid interval: {self.interval}")

        value = int(match.group(1))
        unit = match.group(2)

        # Convert to timedelta
        if unit in ["week", "weeks"]:
            return timedelta(weeks=value)
        return timedelta(days=value)

    def create_interval_text(self, time_delta: timedelta) -> str:
        """
        Create INTERVAL text expression from timedelta using widely-supported SQL notation.

        Uses standard SQL INTERVAL syntax (INTERVAL n DAY/WEEK) which is supported by most
        major databases including PostgreSQL, MySQL, BigQuery, Oracle, and others that follow
        SQL-92 standards.

        The method automatically optimizes intervals:
        - Multiples of 7 days are converted to weeks (e.g., INTERVAL 2 WEEK vs INTERVAL 14 DAY)
        - This provides cleaner, more readable SQL output

        Args:
            time_delta: Python timedelta object to convert to SQL INTERVAL syntax

        Returns:
            String in format "INTERVAL n WEEK" or "INTERVAL n DAY"

        Note:
            Subclasses can override this method to provide database-specific interval syntax
            if needed (e.g., SQL Server uses DATEADD instead of INTERVAL notation).
        """
        total_days = int(time_delta.total_seconds() / 86400)  # 86400 seconds in a day

        # Check if it's a clean week interval
        if total_days % 7 == 0 and total_days >= 7:
            weeks = total_days // 7
            return f"INTERVAL {weeks} WEEK"
        return f"INTERVAL {total_days} DAY"

    def _parse_time_expression(self, expr: str) -> ColumnElement:
        """Convert time expression to SQLAlchemy expression using INTERVAL syntax."""
        expr = expr.strip().upper()

        # Handle NOW()
        if expr == "NOW()":
            return func.current_timestamp()

        # Handle NOW() arithmetic
        now_match = re.match(
            r"^NOW\(\)\s*([+-])\s*(\d+)\s+(DAY|DAYS|WEEK|WEEKS)$", expr
        )
        if now_match:
            operator = now_match.group(1)
            value = int(now_match.group(2))
            unit = now_match.group(3).upper()

            # Create timedelta and convert to clean INTERVAL text
            if unit in ["WEEK", "WEEKS"]:
                time_delta = timedelta(weeks=value)
            else:
                time_delta = timedelta(days=value)

            interval_text = self.create_interval_text(time_delta)
            base_expr = func.current_timestamp()

            if operator == "-":
                return base_expr - text(interval_text)
            return base_expr + text(interval_text)

        # Handle date literals - use func.DATE() for proper date arithmetic
        if re.match(r"^\d{4}-\d{2}-\d{2}", expr):
            # Clean date string and create DATE() function call
            date_str = expr.split()[0]  # Remove time part if present
            return func.DATE(date_str)

        raise ValueError(f"Unsupported time expression: {expr}")

    def _calculate_total_duration(self) -> timedelta:
        """Calculate total duration between start and end as timedelta."""
        start_match = re.match(
            r"^NOW\(\)\s*-\s*(\d+)\s+(DAY|DAYS|WEEK|WEEKS)$", self.start
        )
        end_is_now = str(self.end).upper() == "NOW()"

        # Handle NOW() - X to NOW() pattern
        if start_match and end_is_now:
            value = int(start_match.group(1))
            unit = start_match.group(2).upper()

            if unit in ["WEEK", "WEEKS"]:
                return timedelta(weeks=value)
            return timedelta(days=value)

        # Handle date literal ranges
        start_date_match = re.match(r"^(\d{4}-\d{2}-\d{2})", self.start)
        end_date_match = re.match(r"^(\d{4}-\d{2}-\d{2})", self.end)

        if start_date_match and end_date_match:
            start_date = datetime.strptime(start_date_match.group(1), "%Y-%m-%d")
            end_date = datetime.strptime(end_date_match.group(1), "%Y-%m-%d")

            if end_date <= start_date:
                raise ValueError(
                    f"End date must be after start date: {self.start} to {self.end}"
                )

            return end_date - start_date

        raise ValueError(
            f"Cannot calculate intervals for start='{self.start}' end='{self.end}'"
        )

    def _generate_intervals(
        self, field_column, interval_time_delta: timedelta, total_duration: timedelta
    ) -> List[BinaryExpression]:
        """Generate interval conditions using clean INTERVAL text expressions."""
        conditions = []

        # Check if we're working with NOW() expressions
        is_now_based = (
            "NOW()" in str(self.start).upper() or "NOW()" in str(self.end).upper()
        )

        if is_now_based:
            # Handle NOW() - X to NOW() pattern
            current_offset = total_duration

            # Generate intervals from furthest back to most recent
            while current_offset.total_seconds() > 0:
                start_offset = current_offset
                end_offset = current_offset - interval_time_delta
                if end_offset.total_seconds() < 0:
                    end_offset = timedelta(0)

                # Use clean INTERVAL text expressions
                if start_offset.total_seconds() == 0:
                    start_expr = func.current_timestamp()
                else:
                    start_interval_text = self.create_interval_text(start_offset)
                    start_expr = func.current_timestamp() - text(start_interval_text)

                if end_offset.total_seconds() == 0:
                    # Last interval: use the actual end expression
                    end_expr = self._parse_time_expression(self.end)
                else:
                    end_interval_text = self.create_interval_text(end_offset)
                    end_expr = func.current_timestamp() - text(end_interval_text)

                condition = and_(field_column > start_expr, field_column <= end_expr)
                conditions.append(condition)

                current_offset = end_offset
        else:
            # Handle date literal ranges using INTERVAL arithmetic with func.DATE()
            start_expr = self._parse_time_expression(self.start)
            current_offset = timedelta(0)

            # Generate intervals from start to end
            while current_offset < total_duration:
                if current_offset.total_seconds() == 0:
                    # Use the parsed start expression directly (already wrapped in func.DATE())
                    interval_start = start_expr
                else:
                    # Use INTERVAL text for the offset with proper date arithmetic
                    offset_interval_text = self.create_interval_text(current_offset)
                    interval_start = start_expr + text(offset_interval_text)

                next_offset = current_offset + interval_time_delta
                if next_offset >= total_duration:
                    # Last interval: use actual end (already wrapped in func.DATE())
                    interval_end = self._parse_time_expression(self.end)
                else:
                    # Use INTERVAL text for the next boundary with proper date arithmetic
                    next_interval_text = self.create_interval_text(next_offset)
                    interval_end = start_expr + text(next_interval_text)

                condition = and_(
                    field_column > interval_start, field_column <= interval_end
                )
                conditions.append(condition)

                current_offset = next_offset

        return conditions

    def generate_expressions(self) -> List[BinaryExpression]:
        """
        Generate SQLAlchemy WHERE conditions for time-based partitioning.

        Returns:
            List of SQLAlchemy BinaryExpression conditions for each interval
        """
        field_column = column(self.field)
        interval_time_delta = self._parse_interval()
        total_duration = self._calculate_total_duration()

        # Generate intervals
        return self._generate_intervals(
            field_column, interval_time_delta, total_duration
        )

    def generate_where_clauses(self) -> List[str]:
        """
        Generate SQLAlchemy WHERE conditions for time-based partitioning.
        """
        raise NotImplementedError("generate_where_clauses not implemented")


class BigQueryTimeBasedPartitioning(TimeBasedPartitioning):
    """
    Generates BigQuery-specific WHERE clauses for time-based partitioning.
    """

    def generate_where_clauses(self) -> List[str]:
        """
        Generate BigQuery-specific WHERE clauses.
        """

        bigquery_dialect = BigQueryDialect()
        conditions = self.generate_expressions()

        # Convert SQLAlchemy conditions to string format
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
