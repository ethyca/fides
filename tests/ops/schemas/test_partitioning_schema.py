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
                interval="7 months",  # Not supported
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
            "created_at > CURRENT_TIMESTAMP - INTERVAL 3 WEEK AND created_at <= CURRENT_TIMESTAMP - INTERVAL 2 WEEK",
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
            "created_at > CURRENT_TIMESTAMP - INTERVAL 2 WEEK AND created_at <= CURRENT_TIMESTAMP - INTERVAL 1 WEEK",
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
            "created_at > DATE('2024-01-01') AND created_at <= DATE('2024-01-01') + INTERVAL 1 WEEK",
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
            "created_at > CURRENT_TIMESTAMP - INTERVAL 1 WEEK AND created_at <= CURRENT_TIMESTAMP",
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
            "created_at > CURRENT_TIMESTAMP - INTERVAL 10 DAY AND created_at <= CURRENT_TIMESTAMP - INTERVAL 1 WEEK",
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
            "`created_at` > CURRENT_TIMESTAMP - INTERVAL 30 DAY AND `created_at` <= CURRENT_TIMESTAMP - INTERVAL 20 DAY",
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
            "`created_at` > CURRENT_TIMESTAMP - INTERVAL 1 WEEK AND `created_at` <= CURRENT_TIMESTAMP",
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
            "`created_at` > CURRENT_TIMESTAMP - INTERVAL 30 DAY AND `created_at` <= CURRENT_TIMESTAMP - INTERVAL 25 DAY",
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
            "`created_at` > DATE('2024-01-01') AND `created_at` <= DATE('2024-01-01') + INTERVAL 1 WEEK",
            "`created_at` > DATE('2024-01-01') + INTERVAL 1 WEEK AND `created_at` <= DATE('2024-01-15')",
        ]
