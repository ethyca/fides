"""Tests for post_upgrade_backfill module."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session

from fides.api.migrations.post_upgrade_backfill import (
    BackfillResult,
    acquire_backfill_lock,
    backfill_is_leaf,
    is_transient_error,
    release_backfill_lock,
)
from fides.api.models.detection_discovery.core import StagedResource


class TestBackfillResult:
    """Tests for BackfillResult dataclass."""

    def test_success_property_true_when_no_failures(self):
        """Verify success returns True when no failed batches."""
        result = BackfillResult(
            name="test",
            total_updated=100,
            total_batches=5,
            failed_batches=0,
        )
        assert result.success is True

    def test_success_property_false_when_failures(self):
        """Verify success returns False when there are failures."""
        result = BackfillResult(
            name="test",
            total_updated=80,
            total_batches=5,
            failed_batches=1,
            errors=["Batch 3 failed: connection lost"],
        )
        assert result.success is False

    def test_str_includes_name(self):
        """Verify __str__ includes the backfill name."""
        result = BackfillResult(
            name="is_leaf",
            total_updated=1000,
            total_batches=10,
            failed_batches=0,
        )
        result_str = str(result)
        assert "[is_leaf]" in result_str
        assert "SUCCESS" in result_str
        assert "1000 rows" in result_str
        assert "10 batches" in result_str

    def test_str_with_failures(self):
        """Verify __str__ includes failure information."""
        result = BackfillResult(
            name="test",
            total_updated=80,
            total_batches=5,
            failed_batches=2,
        )
        result_str = str(result)
        assert "COMPLETED WITH ERRORS" in result_str
        assert "2 failed batches" in result_str


class TestIsTransientError:
    """Tests for is_transient_error function."""

    @pytest.mark.parametrize(
        "error,expected",
        [
            # OperationalError is always transient
            (OperationalError("connection lost", None, None), True),
            # DBAPIError with transient indicators
            (DBAPIError("connection refused", None, None), True),
            (DBAPIError("timeout exceeded", None, None), True),
            (DBAPIError("deadlock detected", None, None), True),
            (DBAPIError("lock wait timeout", None, None), True),
            (DBAPIError("too many connections", None, None), True),
            (DBAPIError("server closed the connection", None, None), True),
            (DBAPIError("lost connection to server", None, None), True),
            # DBAPIError without transient indicators
            (DBAPIError("unique constraint violated", None, None), False),
            (DBAPIError("column does not exist", None, None), False),
            # Non-database errors are not transient
            (ValueError("not a db error"), False),
            (RuntimeError("something went wrong"), False),
        ],
    )
    def test_is_transient_error(self, error, expected):
        """Verify is_transient_error correctly identifies transient errors."""
        assert is_transient_error(error) == expected


class TestBackfillLock:
    """Tests for backfill lock functions."""

    @pytest.mark.parametrize(
        "cache_set_return,expected",
        [
            (True, True),  # Lock acquired successfully
            (None, False),  # Lock already held (Redis SET NX returns None if key exists)
        ],
    )
    def test_acquire_backfill_lock(self, cache_set_return, expected):
        """Verify lock acquisition returns correct result based on cache state."""
        mock_cache = MagicMock()
        mock_cache.set.return_value = cache_set_return

        with patch(
            "fides.api.migrations.post_upgrade_backfill.get_cache",
            return_value=mock_cache,
        ):
            result = acquire_backfill_lock()

        assert result is expected
        mock_cache.set.assert_called_once()

    def test_release_backfill_lock(self):
        """Verify lock is released."""
        mock_cache = MagicMock()

        with patch(
            "fides.api.migrations.post_upgrade_backfill.get_cache",
            return_value=mock_cache,
        ):
            release_backfill_lock()

        mock_cache.delete.assert_called_once_with("fides:backfill:running")


class TestBackfillIsLeaf:
    """Tests for backfill_is_leaf function."""

    @pytest.fixture
    def staged_resources_needing_backfill(self, db: Session):
        """Create staged resources that need is_leaf backfill."""
        resources = []

        # Field with no children and no object data_type -> should be leaf (True)
        leaf_field = StagedResource.create(
            db=db,
            data={
                "urn": "test_backfill_monitor.db.schema.table.leaf_field",
                "name": "leaf_field",
                "resource_type": "Field",
                "children": [],
                "meta": {"data_type": "string"},
            },
        )
        # Manually set is_leaf to NULL to simulate pre-migration state
        db.execute(
            StagedResource.__table__.update()
            .where(StagedResource.id == leaf_field.id)
            .values(is_leaf=None)
        )
        db.commit()
        resources.append(leaf_field)

        # Field with object data_type -> should not be leaf (False)
        object_field = StagedResource.create(
            db=db,
            data={
                "urn": "test_backfill_monitor.db.schema.table.object_field",
                "name": "object_field",
                "resource_type": "Field",
                "children": [],
                "meta": {"data_type": "object"},
            },
        )
        db.execute(
            StagedResource.__table__.update()
            .where(StagedResource.id == object_field.id)
            .values(is_leaf=None)
        )
        db.commit()
        resources.append(object_field)

        # Field with children -> should not be leaf (False)
        field_with_children = StagedResource.create(
            db=db,
            data={
                "urn": "test_backfill_monitor.db.schema.table.parent_field",
                "name": "parent_field",
                "resource_type": "Field",
                "children": ["child1", "child2"],
                "meta": {},
            },
        )
        db.execute(
            StagedResource.__table__.update()
            .where(StagedResource.id == field_with_children.id)
            .values(is_leaf=None)
        )
        db.commit()
        resources.append(field_with_children)

        # Table resource -> should not be leaf (False, not a Field)
        table_resource = StagedResource.create(
            db=db,
            data={
                "urn": "test_backfill_monitor.db.schema.table",
                "name": "table",
                "resource_type": "Table",
                "children": [],
            },
        )
        db.execute(
            StagedResource.__table__.update()
            .where(StagedResource.id == table_resource.id)
            .values(is_leaf=None)
        )
        db.commit()
        resources.append(table_resource)

        yield resources

        # Cleanup
        for resource in resources:
            resource.delete(db)

    def test_backfill_no_pending_rows(self, db: Session):
        """Verify no-op when all rows have is_leaf set."""
        # Mock to simulate no pending rows
        with patch(
            "fides.api.migrations.post_upgrade_backfill.get_pending_is_leaf_count",
            return_value=0,
        ):
            result = backfill_is_leaf(db, batch_size=100, batch_delay_seconds=0)

        assert result.name == "is_leaf"
        assert result.total_updated == 0
        assert result.total_batches == 0
        assert result.success is True

    def test_backfill_with_pending_rows(
        self, db: Session, staged_resources_needing_backfill
    ):
        """Verify is_leaf is correctly set based on resource_type, children, and meta."""
        # Run backfill with small batch and no delay for testing
        with patch(
            "fides.api.migrations.post_upgrade_backfill.refresh_backfill_lock"
        ):
            result = backfill_is_leaf(db, batch_size=100, batch_delay_seconds=0)

        assert result.name == "is_leaf"
        assert result.success is True
        assert result.total_updated >= 4  # At least our 4 test resources

        leaf_field = staged_resources_needing_backfill[0]
        object_field = staged_resources_needing_backfill[1]
        field_with_children = staged_resources_needing_backfill[2]
        table_resource = staged_resources_needing_backfill[3]

        for resource in [leaf_field, object_field, field_with_children, table_resource]:
            db.refresh(resource)

        # Field with no children and non-object data_type -> True
        assert leaf_field.is_leaf is True

        # Field with object data_type -> False
        assert object_field.is_leaf is False

        # Field with children -> False
        assert field_with_children.is_leaf is False

        # Table (not a Field) -> False
        assert table_resource.is_leaf is False

    def test_backfill_result_has_correct_name(self, db: Session):
        """Verify the backfill result has the correct name."""
        with patch(
            "fides.api.migrations.post_upgrade_backfill.get_pending_is_leaf_count",
            return_value=0,
        ):
            result = backfill_is_leaf(db, batch_size=100, batch_delay_seconds=0)

        assert result.name == "is_leaf"
