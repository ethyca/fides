"""Tests for post_upgrade_backfill module."""

from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from fides.api.migrations.backfill_scripts.backfill_stagedresource_is_leaf import (
    backfill_stagedresource_is_leaf,
    get_pending_is_leaf_count,
)
from fides.api.models.detection_discovery.core import StagedResource


class TestGetPendingIsLeafCount:
    """Tests for get_pending_is_leaf_count SELECT query."""

    def test_query_filters(self, db: Session):
        """Verify query counts only rows with is_leaf=NULL and valid resource_type."""

        # Resource with is_leaf NOT NULL (should NOT be counted)
        r_not_null = StagedResource.create(
            db=db,
            data={
                "urn": "test.not_null",
                "name": "not_null",
                "resource_type": "Field",
                "children": [],
                "is_leaf": False,
            },
        )

        # Resource with is_leaf=NULL but invalid resource_type (should NOT be counted)
        r_invalid_type = StagedResource.create(
            db=db,
            data={
                "urn": "test.invalid",
                "name": "invalid",
                "resource_type": "Non-datastore",
                "children": [],
                "is_leaf": None,
            },
        )

        # Resources with is_leaf=NULL and valid types (should be counted)
        valid_types = ["Database", "Schema", "Table", "Field", "Endpoint"]
        for resource_type in valid_types:
            r = StagedResource.create(
                db=db,
                data={
                    "urn": f"test.{resource_type.lower()}",
                    "name": resource_type.lower(),
                    "resource_type": resource_type,
                    "children": [],
                    "is_leaf": None,
                },
            )

        # Should count exactly 5 resources (the valid types with is_leaf=NULL)
        assert get_pending_is_leaf_count(db) == 5


class TestBackfillStagedresourceIsLeaf:
    """Tests for backfill_stagedresource_is_leaf function."""

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
                "is_leaf": None,
            },
        )
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
                "is_leaf": None,
            },
        )
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
                "is_leaf": None,
            },
        )
        resources.append(field_with_children)

        # Table resource -> should not be leaf (False, not a Field)
        table_resource = StagedResource.create(
            db=db,
            data={
                "urn": "test_backfill_monitor.db.schema.table",
                "name": "table",
                "resource_type": "Table",
                "children": [],
                "is_leaf": None,
            },
        )
        resources.append(table_resource)

        yield resources

        # Cleanup
        for resource in resources:
            resource.delete(db)

    @patch("fides.api.migrations.backfill_scripts.utils.mark_backfill_completed")
    @patch(
        "fides.api.migrations.backfill_scripts.utils.is_backfill_completed",
        return_value=False,
    )
    def test_backfill_no_pending_rows(
        self, mock_is_completed, mock_mark_completed, db: Session
    ):
        """Verify no-op when all rows have is_leaf set."""
        # Mock to simulate no pending rows
        with patch(
            "fides.api.migrations.backfill_scripts.backfill_stagedresource_is_leaf.get_pending_is_leaf_count",
            return_value=0,
        ):
            result = backfill_stagedresource_is_leaf(
                db, batch_size=100, batch_delay_seconds=0
            )

        assert result.name == "stagedresource-is_leaf"
        assert result.total_updated == 0
        assert result.total_batches == 0
        assert result.success is True

    @patch("fides.api.migrations.backfill_scripts.utils.mark_backfill_completed")
    @patch(
        "fides.api.migrations.backfill_scripts.utils.is_backfill_completed",
        return_value=False,
    )
    def test_backfill_with_pending_rows(
        self,
        mock_is_completed,
        mock_mark_completed,
        db: Session,
        staged_resources_needing_backfill,
    ):
        """Verify is_leaf is correctly set based on resource_type, children, and meta."""
        # Run backfill with small batch and no delay for testing
        with patch("fides.api.migrations.backfill_scripts.utils.refresh_backfill_lock"):
            result = backfill_stagedresource_is_leaf(
                db, batch_size=100, batch_delay_seconds=0
            )

        assert result.name == "stagedresource-is_leaf"
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
