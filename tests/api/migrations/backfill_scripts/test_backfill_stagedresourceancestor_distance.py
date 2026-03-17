"""Tests for backfill_stagedresourceancestor_distance module."""

from unittest.mock import patch

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from fides.api.migrations.backfill_scripts.backfill_stagedresrouceancestor_distance import (
    DISTANCE_CALCULATION_EXPR,
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

    @pytest.mark.parametrize(
        "ancestor_urn,descendant_urn,expected_distance",
        [
            # Basic adjacent relationships
            ("monitor.db", "monitor.db.schema", 1),
            ("monitor.db.schema", "monitor.db.schema.table", 1),
            ("monitor.db.schema.table", "monitor.db.schema.table.field", 1),
            (
                "monitor.db.schema.table.field",
                "monitor.db.schema.table.field.nested",
                1,
            ),
            # Non-adjacent relationships
            ("monitor.db", "monitor.db.schema.table", 2),
            ("monitor.db", "monitor.db.schema.table.field", 3),
            ("monitor.db.schema", "monitor.db.schema.table.field", 2),
            # Deeply nested fields
            ("monitor.db.schema.table", "monitor.db.schema.table.field1.field2", 2),
            (
                "monitor.db.schema.table",
                "monitor.db.schema.table.field1.field2.field3",
                3,
            ),
            (
                "monitor.db.schema.table",
                "monitor.db.schema.table.field1.field2.field3.field4",
                4,
            ),
            (
                "monitor.db",
                "monitor.db.schema.table.field1.field2.field3.field4.field5",
                7,
            ),
            # Nested field to nested field
            (
                "monitor.db.schema.table.field1",
                "monitor.db.schema.table.field1.field2",
                1,
            ),
            (
                "monitor.db.schema.table.field1",
                "monitor.db.schema.table.field1.field2.field3.field4",
                3,
            ),
            (
                "monitor.db.schema.table.field1.field_2",
                "monitor.db.schema.table.field1.field_2.field_3.field_4",
                2,
            ),
            # Without database (e.g. DynamoDB, Salesforce monitors)
            ("monitor.schema", "monitor.schema.table", 1),
            ("monitor.schema", "monitor.schema.table.field", 2),
            ("monitor.schema.table", "monitor.schema.table.field", 1),
            ("monitor.schema.table", "monitor.schema.table.field.nested", 2),
            # URN format validation - separators other than '.' cause incorrect calculations
            # These document that the calculation is tightly coupled to '.' as separator
            (
                "monitor-db-schema",
                "monitor-db-schema-table",
                0,
            ),  # No '.' means 1 segment each = distance 0
            (
                "monitor_db_schema",
                "monitor_db_schema_table",
                0,
            ),  # Underscores not treated as separators
        ],
    )
    def test_urn_segment_distance_calculation(
        self,
        db: Session,
        ancestor_urn: str,
        descendant_urn: str,
        expected_distance: int,
    ):
        """
        Test the URN distance calculation SQL expression in isolation.

        This test verifies the core calculation logic without running the full
        backfill (no UPDATE, batching, or locking). It ensures the SQL correctly
        calculates distance for various URN hierarchies including edge cases like
        deeply nested fields and non-adjacent ancestors.
        """
        # Execute only the calculation part as a SELECT query
        # Convert column names to bind parameters for testing
        calculation_with_params = DISTANCE_CALCULATION_EXPR.replace(
            "descendant_urn", ":descendant_urn"
        ).replace("ancestor_urn", ":ancestor_urn")

        result = db.execute(
            text(f"SELECT ({calculation_with_params}) AS calculated_distance"),
            {"descendant_urn": descendant_urn, "ancestor_urn": ancestor_urn},
        )

        calculated_distance = result.scalar()
        assert calculated_distance == expected_distance, (
            f"Distance calculation failed for {ancestor_urn} -> {descendant_urn}. "
            f"Expected {expected_distance}, got {calculated_distance}"
        )

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
