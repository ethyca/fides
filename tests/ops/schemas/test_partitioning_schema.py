"""
Tests for time-based partitioning schemas.
"""

import pytest

from fides.api.schemas.partitioning import (
    BigQueryTimeBasedPartitioning,
    TimeBasedPartitioning,
)


class TestTimeBasedPartitioning:
    """Test the base TimeBasedPartitioning class."""

    def test_basic_partitioning_validation(self):
        """Test basic validation of partitioning parameters."""
        partitioning = TimeBasedPartitioning(
            field="created_at", start="NOW() - 30 DAYS", end="NOW()", interval="7 days"
        )

        assert partitioning.field == "created_at"
        assert partitioning.start == "NOW() - 30 DAYS"
        assert partitioning.end == "NOW()"
        assert partitioning.interval == "7 days"

    def test_invalid_time_expression(self):
        """Test that invalid time expressions raise validation errors."""
        with pytest.raises(ValueError, match="Unsupported time expression"):
            TimeBasedPartitioning(
                field="created_at", start="INVALID_TIME", end="NOW()", interval="7 days"
            )

    def test_invalid_interval_format(self):
        """Test that invalid interval formats raise validation errors."""
        with pytest.raises(ValueError, match="Invalid interval format"):
            TimeBasedPartitioning(
                field="created_at",
                start="NOW() - 30 DAYS",
                end="NOW()",
                interval="7 fortnights",  # Not supported
            )

    def test_generate_expressions_returns_proper_expression_objects(self):
        """Test that generate_expressions returns proper SQLAlchemy expression objects."""
        partitioning = TimeBasedPartitioning(
            field="created_at", start="NOW() - 21 DAYS", end="NOW()", interval="7 days"
        )

        expressions = partitioning.generate_expressions()

        # Should generate 3 partitions (21 days / 7 days)
        assert len(expressions) == 3

        compiled_expressions = [
            str(expr.compile(compile_kwargs={"literal_binds": True}))
            for expr in expressions
        ]
        assert compiled_expressions == [
            "created_at >= CURRENT_TIMESTAMP - INTERVAL 3 WEEK AND created_at <= CURRENT_TIMESTAMP - INTERVAL 2 WEEK",
            "created_at > CURRENT_TIMESTAMP - INTERVAL 2 WEEK AND created_at <= CURRENT_TIMESTAMP - INTERVAL 1 WEEK",
            "created_at > CURRENT_TIMESTAMP - INTERVAL 1 WEEK AND created_at <= CURRENT_TIMESTAMP",
        ]

    def test_generate_expressions_with_expected_conditions(self):
        """Test generate_expressions returns expected SQLAlchemy conditions."""
        partitioning = TimeBasedPartitioning(
            field="created_at", start="NOW() - 14 DAYS", end="NOW()", interval="7 days"
        )

        expressions = partitioning.generate_expressions()

        # Should generate 2 partitions
        assert len(expressions) == 2

        compiled_expressions = [
            str(expr.compile(compile_kwargs={"literal_binds": True}))
            for expr in expressions
        ]

        assert compiled_expressions == [
            "created_at >= CURRENT_TIMESTAMP - INTERVAL 2 WEEK AND created_at <= CURRENT_TIMESTAMP - INTERVAL 1 WEEK",
            "created_at > CURRENT_TIMESTAMP - INTERVAL 1 WEEK AND created_at <= CURRENT_TIMESTAMP",
        ]

    def test_generate_expressions_with_date_literals(self):
        """Test generate_expressions with date literal start/end times."""
        partitioning = TimeBasedPartitioning(
            field="created_at", start="2024-01-01", end="2024-01-15", interval="7 days"
        )

        expressions = partitioning.generate_expressions()

        # Should generate 2 partitions (14 days / 7 days)
        assert len(expressions) == 2

        compiled_expressions = [
            str(expr.compile(compile_kwargs={"literal_binds": True}))
            for expr in expressions
        ]

        assert compiled_expressions == [
            "created_at >= DATE('2024-01-01') AND created_at <= DATE('2024-01-01') + INTERVAL 1 WEEK",
            "created_at > DATE('2024-01-01') + INTERVAL 1 WEEK AND created_at <= DATE('2024-01-15')",
        ]

    def test_single_partition_scenario(self):
        """Test scenario where interval equals total duration (single partition)."""
        partitioning = TimeBasedPartitioning(
            field="created_at", start="NOW() - 7 DAYS", end="NOW()", interval="7 days"
        )

        expressions = partitioning.generate_expressions()

        # Should generate only 1 partition
        assert len(expressions) == 1

        compiled_expressions = [
            str(expr.compile(compile_kwargs={"literal_binds": True}))
            for expr in expressions
        ]
        assert compiled_expressions == [
            "created_at >= CURRENT_TIMESTAMP - INTERVAL 1 WEEK AND created_at <= CURRENT_TIMESTAMP",
        ]

    def test_generate_expressions_with_non_week_intervals(self):
        """Test generate_expressions with intervals that don't convert to weeks."""
        partitioning = TimeBasedPartitioning(
            field="created_at", start="NOW() - 10 DAYS", end="NOW()", interval="3 days"
        )

        expressions = partitioning.generate_expressions()

        # Should generate 4 partitions
        assert len(expressions) == 4

        compiled_expressions = [
            str(expr.compile(compile_kwargs={"literal_binds": True}))
            for expr in expressions
        ]
        # The implementation converts 7 days to 1 week
        assert compiled_expressions == [
            "created_at >= CURRENT_TIMESTAMP - INTERVAL 10 DAY AND created_at <= CURRENT_TIMESTAMP - INTERVAL 1 WEEK",
            "created_at > CURRENT_TIMESTAMP - INTERVAL 1 WEEK AND created_at <= CURRENT_TIMESTAMP - INTERVAL 4 DAY",
            "created_at > CURRENT_TIMESTAMP - INTERVAL 4 DAY AND created_at <= CURRENT_TIMESTAMP - INTERVAL 1 DAY",
            "created_at > CURRENT_TIMESTAMP - INTERVAL 1 DAY AND created_at <= CURRENT_TIMESTAMP",
        ]


class TestBigQueryTimeBasedPartitioning:
    """Test the BigQuery-specific partitioning class."""

    def test_generate_where_clauses(self):
        """Test that generate_where_clauses returns string clauses, not SQLAlchemy objects."""
        partitioning = BigQueryTimeBasedPartitioning(
            field="created_at", start="NOW() - 30 DAYS", end="NOW()", interval="10 days"
        )

        clauses = partitioning.generate_where_clauses()

        # Should generate 3 partitions (30 days / 10 days)
        assert len(clauses) == 3
        assert clauses == [
            "`created_at` >= CURRENT_TIMESTAMP - INTERVAL 30 DAY AND `created_at` <= CURRENT_TIMESTAMP - INTERVAL 20 DAY",
            "`created_at` > CURRENT_TIMESTAMP - INTERVAL 20 DAY AND `created_at` <= CURRENT_TIMESTAMP - INTERVAL 10 DAY",
            "`created_at` > CURRENT_TIMESTAMP - INTERVAL 10 DAY AND `created_at` <= CURRENT_TIMESTAMP",
        ]

    def test_generate_where_clauses_single_partition(self):
        """Test scenario where interval equals total duration (single partition)."""
        partitioning = BigQueryTimeBasedPartitioning(
            field="created_at", start="NOW() - 7 DAYS", end="NOW()", interval="7 days"
        )

        clauses = partitioning.generate_where_clauses()
        assert len(clauses) == 1
        assert clauses == [
            "`created_at` >= CURRENT_TIMESTAMP - INTERVAL 1 WEEK AND `created_at` <= CURRENT_TIMESTAMP",
        ]

    def test_generate_where_clauses_many_partitions(self):
        """Test scenario with many small partitions."""
        partitioning = BigQueryTimeBasedPartitioning(
            field="created_at", start="NOW() - 30 DAYS", end="NOW()", interval="5 days"
        )

        clauses = partitioning.generate_where_clauses()

        # Should have 6 partitions (30 days / 5 days)
        assert len(clauses) == 6
        assert clauses == [
            "`created_at` >= CURRENT_TIMESTAMP - INTERVAL 30 DAY AND `created_at` <= CURRENT_TIMESTAMP - INTERVAL 25 DAY",
            "`created_at` > CURRENT_TIMESTAMP - INTERVAL 25 DAY AND `created_at` <= CURRENT_TIMESTAMP - INTERVAL 20 DAY",
            "`created_at` > CURRENT_TIMESTAMP - INTERVAL 20 DAY AND `created_at` <= CURRENT_TIMESTAMP - INTERVAL 15 DAY",
            "`created_at` > CURRENT_TIMESTAMP - INTERVAL 15 DAY AND `created_at` <= CURRENT_TIMESTAMP - INTERVAL 10 DAY",
            "`created_at` > CURRENT_TIMESTAMP - INTERVAL 10 DAY AND `created_at` <= CURRENT_TIMESTAMP - INTERVAL 5 DAY",
            "`created_at` > CURRENT_TIMESTAMP - INTERVAL 5 DAY AND `created_at` <= CURRENT_TIMESTAMP",
        ]

    def test_generate_where_clauses_with_date_literals(self):
        """Test generate_where_clauses with date literal start/end times."""
        partitioning = BigQueryTimeBasedPartitioning(
            field="created_at", start="2024-01-01", end="2024-01-15", interval="7 days"
        )

        clauses = partitioning.generate_where_clauses()

        # Should generate 2 partitions
        assert len(clauses) == 2
        # Now uses proper DATE() + INTERVAL syntax
        assert clauses == [
            "`created_at` >= DATE('2024-01-01') AND `created_at` <= DATE('2024-01-01') + INTERVAL 1 WEEK",
            "`created_at` > DATE('2024-01-01') + INTERVAL 1 WEEK AND `created_at` <= DATE('2024-01-15')",
        ]


# ---------------------------------------------------------------------------
# New tests for list-based partitioning behaviour
# ---------------------------------------------------------------------------


class TestPartitioningList:
    """Tests related to a list of TimeBasedPartitioning specs."""

    def test_validate_partitioning_list_no_overlap(self):
        """A list of non-overlapping specs should pass validation."""
        from fides.api.schemas.partitioning import validate_partitioning_list

        p1 = TimeBasedPartitioning(
            field="created_at",
            start="2024-01-01",
            end="2024-01-15",
            interval="7 days",
        )
        p2 = TimeBasedPartitioning(
            field="created_at",
            start="2024-02-01",
            end="2024-02-15",
            interval="7 days",
        )

        # Should not raise
        validate_partitioning_list([p1, p2])

    def test_validate_partitioning_list_with_overlap(self):
        """Validation should fail if the date ranges overlap."""
        from fides.api.schemas.partitioning import validate_partitioning_list

        p1 = TimeBasedPartitioning(
            field="created_at",
            start="2024-01-01",
            end="2024-01-15",
            interval="7 days",
        )
        p2 = TimeBasedPartitioning(
            field="created_at",
            start="2024-01-10",
            end="2024-01-20",
            interval="7 days",
        )

        with pytest.raises(
            ValueError,
            match="overlap",
        ):
            validate_partitioning_list([p1, p2])

    def test_validate_partitioning_list_open_start_non_overlap(self):
        """Open-start that ends the day before the next spec begins is valid."""
        from fides.api.schemas.partitioning import validate_partitioning_list

        p_open_start = TimeBasedPartitioning(field="created_at", end="2023-12-31")
        p_closed = TimeBasedPartitioning(
            field="created_at",
            start="2024-01-01",
            end="2024-01-15",
            interval="7 days",
        )

        validate_partitioning_list([p_open_start, p_closed])

    def test_adjacent_partition_boundary_no_overlap(self):
        """Two specs where next.start == prev.end should not raise and should compile to non-overlapping clauses."""
        from fides.api.schemas.partitioning import validate_partitioning_list

        prev = TimeBasedPartitioning(
            field="created_at",
            start="2024-01-01",
            end="2024-01-31",
            interval="1 month",
        )

        nxt = TimeBasedPartitioning(
            field="created_at",
            start="2024-01-31",
            end="2024-02-28",
            interval="1 month",
        )

        validate_partitioning_list([prev, nxt])

        clauses_prev = [
            str(e.compile(compile_kwargs={"literal_binds": True}))
            for e in prev.generate_expressions()
        ]
        clauses_nxt = [
            str(e.compile(compile_kwargs={"literal_binds": True}))
            for e in nxt.generate_expressions()
        ]

        # prev ends with <= 2024-01-31, next starts with > 2024-01-31
        assert clauses_prev[-1].endswith("<= DATE('2024-01-31')")
        assert "> DATE('2024-01-31')" in clauses_nxt[0]

    def test_open_start_adjacent_boundary(self):
        """Open-start plus closed spec sharing boundary should validate and be non-overlapping."""
        from fides.api.schemas.partitioning import validate_partitioning_list

        p_open_start = TimeBasedPartitioning(field="created_at", end="2024-01-01")
        p_closed = TimeBasedPartitioning(
            field="created_at",
            start="2024-01-01",
            end="2024-01-15",
            interval="7 days",
        )

        # Should not raise
        validate_partitioning_list([p_open_start, p_closed])

        clauses_open = [
            str(e.compile(compile_kwargs={"literal_binds": True}))
            for e in p_open_start.generate_expressions()
        ]
        clauses_closed = [
            str(e.compile(compile_kwargs={"literal_binds": True}))
            for e in p_closed.generate_expressions()
        ]

        # open slice ends inclusive at 2024-01-01; closed slice starts exclusive > 2024-01-01
        assert clauses_open[-1].endswith("<= DATE('2024-01-01')")
        assert "> DATE('2024-01-01')" in clauses_closed[0]


class TestOpenEndedPartitioning:
    """Cover scenarios where only one bound (start or end) is supplied."""

    def test_generate_expressions_open_start(self):
        """Only `end` provided should yield a single "<=" clause."""
        partitioning = TimeBasedPartitioning(field="created_at", end="NOW()")

        expressions = partitioning.generate_expressions()

        assert len(expressions) == 1

        compiled = str(expressions[0].compile(compile_kwargs={"literal_binds": True}))
        assert compiled == "created_at <= CURRENT_TIMESTAMP"

    def test_generate_expressions_open_end(self):
        """Only `start` provided – should yield a single ">=" clause."""
        partitioning = TimeBasedPartitioning(
            field="created_at", start="NOW() - 30 DAYS"
        )

        expressions = partitioning.generate_expressions()

        assert len(expressions) == 1

        compiled = str(expressions[0].compile(compile_kwargs={"literal_binds": True}))
        assert compiled == "created_at >= CURRENT_TIMESTAMP - INTERVAL 30 DAY"

    def test_missing_interval_error(self):
        """Providing both start and end without interval should raise."""
        with pytest.raises(ValueError, match="interval must be provided"):
            TimeBasedPartitioning(
                field="created_at", start="2024-01-01", end="2024-01-15"
            )


class TestOpenEndedPartitioningBigQuery:
    """BigQuery dialect rendering for open-ended specs."""

    def test_generate_where_clauses_open_end(self):
        partitioning = BigQueryTimeBasedPartitioning(
            field="created_at", start="NOW() - 30 DAYS"
        )

        clauses = partitioning.generate_where_clauses()

        assert clauses == [
            "`created_at` >= CURRENT_TIMESTAMP - INTERVAL 30 DAY",
        ]

    def test_generate_where_clauses_open_start(self):
        partitioning = BigQueryTimeBasedPartitioning(
            field="created_at", end="2024-01-01"
        )

        clauses = partitioning.generate_where_clauses()

        assert clauses == [
            "`created_at` <= DATE('2024-01-01')",
        ]


class TestMonthYearIntervals:
    """Ensure month/year intervals validate and generate correct partitions."""

    def test_interval_validation_month_year(self):
        """Validator should accept month and year units and reject fractions."""
        # Valid
        TimeBasedPartitioning(
            field="created_at", start="2023-01-01", end="2023-04-01", interval="1 month"
        )
        TimeBasedPartitioning(
            field="created_at", start="2020-01-01", end="2022-01-01", interval="2 years"
        )

        # Invalid fractional interval
        with pytest.raises(ValueError):
            TimeBasedPartitioning(
                field="created_at",
                start="2023-01-01",
                end="2023-04-01",
                interval="1.5 months",
            )

    def test_generate_expressions_month_literal(self):
        """Literal start/end with 1-month interval should split correctly."""
        partitioning = TimeBasedPartitioning(
            field="created_at",
            start="2024-01-01",
            end="2024-04-01",
            interval="1 month",
        )

        exprs = partitioning.generate_expressions()

        assert len(exprs) == 3

        compiled = [
            str(e.compile(compile_kwargs={"literal_binds": True})) for e in exprs
        ]

        assert compiled == [
            "created_at >= DATE('2024-01-01') AND created_at <= DATE('2024-01-01') + INTERVAL 1 MONTH",
            "created_at > DATE('2024-01-01') + INTERVAL 1 MONTH AND created_at <= DATE('2024-01-01') + INTERVAL 2 MONTH",
            "created_at > DATE('2024-01-01') + INTERVAL 2 MONTH AND created_at <= DATE('2024-04-01')",
        ]

    def test_generate_where_clauses_year_bigquery(self):
        """BigQuery clauses for 1-year interval over 2 years should split."""
        partitioning = BigQueryTimeBasedPartitioning(
            field="created_at",
            start="2020-01-01",
            end="2022-01-01",
            interval="1 year",
        )

        clauses = partitioning.generate_where_clauses()

        assert len(clauses) == 2

        assert clauses == [
            "`created_at` >= DATE('2020-01-01') AND `created_at` <= DATE('2020-01-01') + INTERVAL 1 YEAR",
            "`created_at` > DATE('2020-01-01') + INTERVAL 1 YEAR AND `created_at` <= DATE('2022-01-01')",
        ]

    def test_dynamic_now_month_interval(self):
        """NOW()-based month range should compile to single clause (no slicing yet)."""
        partitioning = TimeBasedPartitioning(
            field="created_at",
            start="NOW() - 12 MONTHS",
            end="NOW()",
            interval="6 months",
        )

        exprs = partitioning.generate_expressions()
        assert len(exprs) == 2

        compiled = [
            str(e.compile(compile_kwargs={"literal_binds": True})) for e in exprs
        ]
        assert compiled == [
            "created_at >= CURRENT_TIMESTAMP - INTERVAL 12 MONTH AND created_at <= CURRENT_TIMESTAMP - INTERVAL 6 MONTH",
            "created_at > CURRENT_TIMESTAMP - INTERVAL 6 MONTH AND created_at <= CURRENT_TIMESTAMP",
        ]


class TestTodayExpressions:
    def test_today_range_slicing(self):
        part = TimeBasedPartitioning(
            field="event_date",
            start="TODAY() - 30 DAYS",
            end="TODAY()",
            interval="10 days",
        )

        exprs = [
            str(e.compile(compile_kwargs={"literal_binds": True}))
            for e in part.generate_expressions()
        ]

        assert exprs == [
            "event_date >= CURRENT_DATE - INTERVAL 30 DAY AND event_date <= CURRENT_DATE - INTERVAL 20 DAY",
            "event_date > CURRENT_DATE - INTERVAL 20 DAY AND event_date <= CURRENT_DATE - INTERVAL 10 DAY",
            "event_date > CURRENT_DATE - INTERVAL 10 DAY AND event_date <= CURRENT_DATE",
        ]

    def test_today_open_start(self):
        part = TimeBasedPartitioning(field="event_date", end="TODAY()")
        compiled = str(
            part.generate_expressions()[0].compile(
                compile_kwargs={"literal_binds": True}
            )
        )
        assert compiled == "event_date <= CURRENT_DATE"
