"""Tests for backfill_stagedresourceancestor_distance module."""

from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from fides.api.migrations.backfill_scripts.backfill_stagedresrouceancestor_distance import (
    backfill_stagedresourceancestor_distance,
    get_pending_distance_count,
)
from fides.api.models.detection_discovery.core import (
    StagedResource,
    StagedResourceAncestor,
)


class TestGetPendingDistanceCount:
    """Tests for get_pending_distance_count SELECT query."""

    def test_query_filters(self, db: Session):
        """Verify query counts only rows with distance=NULL."""
        # Create staged resources
        db_resource = StagedResource.create(
            db=db,
            data={
                "urn": "test_monitor.db",
                "name": "db",
                "resource_type": "Database",
                "children": [],
            },
        )
        schema_resource = StagedResource.create(
            db=db,
            data={
                "urn": "test_monitor.db.schema",
                "name": "schema",
                "resource_type": "Schema",
                "children": [],
            },
        )
        table_resource = StagedResource.create(
            db=db,
            data={
                "urn": "test_monitor.db.schema.table",
                "name": "table",
                "resource_type": "Table",
                "children": [],
            },
        )

        # Relationship with distance=NULL (should be counted)
        rel_null = StagedResourceAncestor(
            ancestor_urn=db_resource.urn,
            descendant_urn=table_resource.urn,
            distance=None,
        )
        db.add(rel_null)

        # Relationship with distance already set (should NOT be counted)
        rel_set = StagedResourceAncestor(
            ancestor_urn=db_resource.urn,
            descendant_urn=schema_resource.urn,
            distance=1,
        )
        db.add(rel_set)
        db.commit()

        count = get_pending_distance_count(db)

        # Only rel_null should be counted (distance=NULL)
        assert count == 1


class TestBackfillStagedresourceancestorDistance:
    """Tests for backfill_stagedresourceancestor_distance function."""

    @pytest.fixture
    def ancestor_relationships_needing_backfill(self, db: Session):
        """Create ancestor relationships that need distance backfill."""
        # Create staged resources with hierarchical URNs
        db_resource = StagedResource.create(
            db=db,
            data={
                "urn": "test_monitor.db",
                "name": "db",
                "resource_type": "Database",
                "children": [],
            },
        )
        schema_resource = StagedResource.create(
            db=db,
            data={
                "urn": "test_monitor.db.schema",
                "name": "schema",
                "resource_type": "Schema",
                "children": [],
            },
        )
        table_resource = StagedResource.create(
            db=db,
            data={
                "urn": "test_monitor.db.schema.table",
                "name": "table",
                "resource_type": "Table",
                "children": [],
            },
        )
        field_resource = StagedResource.create(
            db=db,
            data={
                "urn": "test_monitor.db.schema.table.field",
                "name": "field",
                "resource_type": "Field",
                "children": [],
            },
        )

        # Create ancestor relationships with distance=NULL
        db.add(
            StagedResourceAncestor(
                ancestor_urn=schema_resource.urn,
                descendant_urn=table_resource.urn,
                distance=None,
            )
        )
        db.add(
            StagedResourceAncestor(
                ancestor_urn=db_resource.urn,
                descendant_urn=table_resource.urn,
                distance=None,
            )
        )
        db.add(
            StagedResourceAncestor(
                ancestor_urn=db_resource.urn,
                descendant_urn=field_resource.urn,
                distance=None,
            )
        )

        db.commit()

        yield db_resource, schema_resource, table_resource, field_resource

    @patch("fides.api.migrations.backfill_scripts.utils.mark_backfill_completed")
    @patch(
        "fides.api.migrations.backfill_scripts.utils.is_backfill_completed",
        return_value=False,
    )
    def test_backfill_no_pending_rows(
        self, mock_is_completed, mock_mark_completed, db: Session
    ):
        """Verify no-op when all rows have distance set."""
        with patch(
            "fides.api.migrations.backfill_scripts.backfill_stagedresrouceancestor_distance.get_pending_distance_count",
            return_value=0,
        ):
            result = backfill_stagedresourceancestor_distance(
                db, batch_size=100, batch_delay_seconds=0
            )

        assert result.name == "stagedresourceancestor-distance"
        assert result.total_updated == 0
        assert result.total_batches == 0
        assert result.success is True

    @patch("fides.api.migrations.backfill_scripts.utils.mark_backfill_completed")
    @patch(
        "fides.api.migrations.backfill_scripts.utils.is_backfill_completed",
        return_value=False,
    )
    def test_backfill_calculates_distance_from_urns(
        self,
        mock_is_completed,
        mock_mark_completed,
        db: Session,
        ancestor_relationships_needing_backfill,
    ):
        """Verify distance is calculated correctly from URN segments."""
        db_resource, schema_resource, table_resource, field_resource = (
            ancestor_relationships_needing_backfill
        )

        # Run backfill
        with patch("fides.api.migrations.backfill_scripts.utils.refresh_backfill_lock"):
            result = backfill_stagedresourceancestor_distance(
                db, batch_size=100, batch_delay_seconds=0
            )

        assert result.name == "stagedresourceancestor-distance"
        assert result.success is True
        assert result.total_updated == 3  # At least our 3 test relationships

        # Query the relationships to verify distances
        rel1 = (
            db.query(StagedResourceAncestor)
            .filter_by(
                ancestor_urn=schema_resource.urn, descendant_urn=table_resource.urn
            )
            .first()
        )
        rel2 = (
            db.query(StagedResourceAncestor)
            .filter_by(ancestor_urn=db_resource.urn, descendant_urn=table_resource.urn)
            .first()
        )
        rel3 = (
            db.query(StagedResourceAncestor)
            .filter_by(ancestor_urn=db_resource.urn, descendant_urn=field_resource.urn)
            .first()
        )

        # Verify distance calculations
        assert rel1.distance == 1  # schema -> table
        assert rel2.distance == 2  # db -> table
        assert rel3.distance == 3  # db -> field
