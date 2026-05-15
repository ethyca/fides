# pylint: disable=redefined-outer-name
"""Tests for CloudInfraGroup and CloudInfraGroupAssignment ORM models."""

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.detection_discovery.cloud_infra import CloudInfraStagedResource
from fides.api.models.detection_discovery.cloud_infra_group import (
    CloudInfraGroup,
    CloudInfraGroupAssignment,
)
from fides.api.models.detection_discovery.core import DiffStatus, StagedResourceType
from fides.api.models.sql_models import System  # type: ignore[attr-defined]


def _create_system(db: Session) -> System:
    """Create a minimal System for testing."""
    system = System.create(
        db=db,
        data={
            "fides_key": f"test_system_{uuid4()}",
            "name": f"Test System {uuid4()}",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )
    return system


class TestCloudInfraGroupModel:
    MONITOR_KEY = "aws_monitor_1"

    @pytest.fixture
    def group(self, db: Session):
        group = CloudInfraGroup.create(
            db=db,
            data={
                "monitor_config_id": self.MONITOR_KEY,
                "name": "Checkout Service",
            },
        )
        yield group
        db.delete(group)
        db.commit()

    def test_create_with_draft_name(self, db: Session, group: CloudInfraGroup):
        assert group.monitor_config_id == self.MONITOR_KEY
        assert group.name == "Checkout Service"
        assert group.system_id is None

    def test_create_without_system_id(self, db: Session, group: CloudInfraGroup):
        fetched = db.query(CloudInfraGroup).filter_by(id=group.id).one()
        assert fetched.system_id is None
        assert fetched.name == "Checkout Service"

    def test_unique_system_per_monitor(self, db: Session):
        """Two groups from the same monitor cannot target the same System."""
        system = _create_system(db)
        g1 = CloudInfraGroup.create(
            db=db,
            data={
                "monitor_config_id": self.MONITOR_KEY,
                "system_id": system.id,
            },
        )
        with pytest.raises(IntegrityError):
            CloudInfraGroup.create(
                db=db,
                data={
                    "monitor_config_id": self.MONITOR_KEY,
                    "system_id": system.id,
                },
            )
        db.rollback()
        db.delete(g1)
        db.delete(system)
        db.commit()

    def test_same_system_different_monitors_allowed(self, db: Session):
        """Different monitors can target the same System."""
        system = _create_system(db)
        g1 = CloudInfraGroup.create(
            db=db,
            data={
                "monitor_config_id": "monitor_a",
                "system_id": system.id,
            },
        )
        g2 = CloudInfraGroup.create(
            db=db,
            data={
                "monitor_config_id": "monitor_b",
                "system_id": system.id,
            },
        )
        assert g1.system_id == g2.system_id == system.id
        db.delete(g1)
        db.delete(g2)
        db.delete(system)
        db.commit()

    def test_multiple_draft_groups_same_monitor_allowed(self, db: Session):
        """Multiple groups with system_id=NULL are allowed for the same monitor
        (partial unique index only applies when system_id IS NOT NULL)."""
        g1 = CloudInfraGroup.create(
            db=db,
            data={
                "monitor_config_id": self.MONITOR_KEY,
                "name": "Draft A",
            },
        )
        g2 = CloudInfraGroup.create(
            db=db,
            data={
                "monitor_config_id": self.MONITOR_KEY,
                "name": "Draft B",
            },
        )
        assert g1.system_id is None
        assert g2.system_id is None
        db.delete(g1)
        db.delete(g2)
        db.commit()


class TestCloudInfraGroupAssignmentModel:
    MONITOR_KEY = "aws_monitor_1"

    @pytest.fixture
    def resource(self, db: Session):
        resource = CloudInfraStagedResource.create(
            db=db,
            data={
                "urn": f"{self.MONITOR_KEY}:arn:aws:s3:::test-bucket",
                "name": "test-bucket",
                "resource_type": StagedResourceType.CLOUD_INFRA,
                "monitor_config_id": self.MONITOR_KEY,
                "diff_status": DiffStatus.ADDITION.value,
                "service": "s3",
                "location": "us-east-1",
                "cloud_account_id": "123456789012",
                "source_id": "arn:aws:s3:::test-bucket",
            },
        )
        yield resource
        db.delete(resource)
        db.commit()

    @pytest.fixture
    def group(self, db: Session):
        group = CloudInfraGroup.create(
            db=db,
            data={
                "monitor_config_id": self.MONITOR_KEY,
                "name": "Test Group",
            },
        )
        yield group
        db.delete(group)
        db.commit()

    @pytest.fixture
    def assignment(
        self,
        db: Session,
        group: CloudInfraGroup,
        resource: CloudInfraStagedResource,
    ):
        assignment = CloudInfraGroupAssignment.create(
            db=db,
            data={
                "resource_id": resource.id,
                "group_id": group.id,
            },
        )
        yield assignment
        # No cleanup needed — cascades from group or resource deletion

    def test_create_assignment(
        self, db: Session, assignment: CloudInfraGroupAssignment, group, resource
    ):
        assert assignment.resource_id == resource.id
        assert assignment.group_id == group.id
        assert assignment.promoted is False

    def test_unique_constraint_resource_group(
        self,
        db: Session,
        assignment: CloudInfraGroupAssignment,
        group: CloudInfraGroup,
        resource: CloudInfraStagedResource,
    ):
        """(resource_id, group_id) must be unique."""
        with pytest.raises(IntegrityError):
            CloudInfraGroupAssignment.create(
                db=db,
                data={
                    "resource_id": resource.id,
                    "group_id": group.id,
                },
            )
        db.rollback()

    def test_cascade_delete_on_group(
        self,
        db: Session,
        group: CloudInfraGroup,
        assignment: CloudInfraGroupAssignment,
    ):
        """Deleting a group cascades to its assignments."""
        assignment_id = assignment.id
        db.delete(group)
        db.commit()

        assert (
            db.query(CloudInfraGroupAssignment).filter_by(id=assignment_id).first()
            is None
        )

    def test_cascade_delete_on_resource(
        self,
        db: Session,
        resource: CloudInfraStagedResource,
        assignment: CloudInfraGroupAssignment,
    ):
        """Deleting a resource cascades to its assignments."""
        assignment_id = assignment.id
        db.delete(resource)
        db.commit()

        assert (
            db.query(CloudInfraGroupAssignment).filter_by(id=assignment_id).first()
            is None
        )

    def test_resource_in_multiple_groups(
        self,
        db: Session,
        resource: CloudInfraStagedResource,
        group: CloudInfraGroup,
    ):
        """A resource can belong to multiple groups."""
        group_b = CloudInfraGroup.create(
            db=db,
            data={
                "monitor_config_id": self.MONITOR_KEY,
                "name": "Group B",
            },
        )
        a1 = CloudInfraGroupAssignment.create(
            db=db,
            data={"resource_id": resource.id, "group_id": group.id},
        )
        a2 = CloudInfraGroupAssignment.create(
            db=db,
            data={"resource_id": resource.id, "group_id": group_b.id},
        )

        assignments = (
            db.query(CloudInfraGroupAssignment).filter_by(resource_id=resource.id).all()
        )
        assert len(assignments) == 2

        # Cleanup
        db.delete(a1)
        db.delete(a2)
        db.delete(group_b)
        db.commit()


class TestUnlinkGroupsOnSystemDelete:
    """Tests for the _unlink_groups_on_system_delete before_delete listener."""

    MONITOR_KEY = "aws_monitor_1"

    def test_system_delete_unlinks_groups_and_resets_assignments(self, db: Session):
        """Full scenario: deleting a System reverts groups to draft, resets
        promoted flags, preserves the System name, and only reverts diff_status
        on resources that have no remaining promoted assignments elsewhere.

        Setup:
        - system (to be deleted)
        - group_a → targets system, name is NULL
        - group_b → draft group (unaffected)
        - resource_only_here → promoted in group_a only (should revert to ADDITION)
        - resource_also_elsewhere → promoted in group_a AND group_b (should stay MONITORED)
        """
        system = _create_system(db)
        system_name = system.name

        def _make_resource(suffix: str) -> CloudInfraStagedResource:
            return CloudInfraStagedResource.create(
                db=db,
                data={
                    "urn": f"{self.MONITOR_KEY}:arn:aws:s3:::bucket-{suffix}",
                    "name": f"bucket-{suffix}",
                    "resource_type": StagedResourceType.CLOUD_INFRA,
                    "monitor_config_id": self.MONITOR_KEY,
                    "diff_status": DiffStatus.MONITORED.value,
                    "service": "s3",
                    "location": "us-east-1",
                    "cloud_account_id": "123456789012",
                    "source_id": f"arn:aws:s3:::bucket-{suffix}",
                },
            )

        resource_only_here = _make_resource("only-here")
        resource_also_elsewhere = _make_resource("also-elsewhere")

        # Group A targets the system being deleted (no name)
        group_a = CloudInfraGroup.create(
            db=db,
            data={
                "monitor_config_id": self.MONITOR_KEY,
                "system_id": system.id,
            },
        )
        assign_a1 = CloudInfraGroupAssignment.create(
            db=db,
            data={
                "resource_id": resource_only_here.id,
                "group_id": group_a.id,
                "promoted": True,
            },
        )
        assign_a2 = CloudInfraGroupAssignment.create(
            db=db,
            data={
                "resource_id": resource_also_elsewhere.id,
                "group_id": group_a.id,
                "promoted": True,
            },
        )

        # Group B is a draft group — resource_also_elsewhere is promoted here too
        group_b = CloudInfraGroup.create(
            db=db,
            data={
                "monitor_config_id": self.MONITOR_KEY,
                "name": "Other Group",
            },
        )
        CloudInfraGroupAssignment.create(
            db=db,
            data={
                "resource_id": resource_also_elsewhere.id,
                "group_id": group_b.id,
                "promoted": True,
            },
        )

        # Act
        db.delete(system)
        db.commit()

        # Refresh ORM objects
        db.refresh(group_a)
        db.refresh(assign_a1)
        db.refresh(assign_a2)
        db.refresh(resource_only_here)
        db.refresh(resource_also_elsewhere)

        # Group A reverted to draft, System name backfilled via COALESCE
        assert group_a.system_id is None
        assert group_a.name == system_name

        # Promoted flags reset on group_a's assignments
        assert assign_a1.promoted is False
        assert assign_a2.promoted is False

        # Resource only in group_a → reverted to ADDITION
        assert resource_only_here.diff_status == DiffStatus.ADDITION.value

        # Resource also promoted in group_b → stays MONITORED
        assert resource_also_elsewhere.diff_status == DiffStatus.MONITORED.value

        # Cleanup
        db.delete(group_a)
        db.delete(group_b)
        db.delete(resource_only_here)
        db.delete(resource_also_elsewhere)
        db.commit()
