import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.detection_discovery.cloud_infra import CloudInfraStagedResource
from fides.api.models.detection_discovery.core import DiffStatus, StagedResourceType


class TestCloudInfraStagedResourceModel:
    MONITOR_KEY = "aws_monitor_1"

    @pytest.fixture
    def create_cloud_infra_resource(self, db: Session) -> CloudInfraStagedResource:
        resource = CloudInfraStagedResource.create(
            db=db,
            data={
                "urn": f"{self.MONITOR_KEY}.arn:aws:s3:my-bucket",
                "name": "my-bucket",
                "resource_type": StagedResourceType.CLOUD_INFRA,
                "monitor_config_id": self.MONITOR_KEY,
                "diff_status": DiffStatus.ADDITION.value,
                "service": "s3",
                "location": "us-east-1",
                "cloud_account_id": "123456789012",
                "source_id": "arn:aws:s3:my-bucket",
                "tags": {"env": "prod", "team": "platform"},
                "meta": {"provider": "aws", "source_type": "s3:bucket", "category": "Storage"},
            },
        )
        return resource

    def test_unique_constraint_monitor_config_and_source_id(
        self, db: Session, create_cloud_infra_resource: CloudInfraStagedResource
    ) -> None:
        """(monitor_config_id, source_id) must be unique."""
        with pytest.raises(IntegrityError):
            CloudInfraStagedResource.create(
                db=db,
                data={
                    "urn": f"{self.MONITOR_KEY}.arn:aws:s3:my-bucket-duplicate",  # different URN
                    "name": "my-bucket-duplicate",
                    "resource_type": StagedResourceType.CLOUD_INFRA,
                    "monitor_config_id": self.MONITOR_KEY,  # same monitor
                    "service": "s3",
                    "location": "us-east-1",
                    "cloud_account_id": "123456789012",
                    "source_id": "arn:aws:s3:my-bucket",  # same source_id → violates constraint
                },
            )
            db.flush()

    def test_same_source_id_different_monitors_is_allowed(
        self, db: Session, create_cloud_infra_resource: CloudInfraStagedResource
    ) -> None:
        """Same source_id is allowed when the monitor_config_id differs."""
        other_monitor = "aws_monitor_2"
        resource = CloudInfraStagedResource.create(
            db=db,
            data={
                "urn": f"{other_monitor}.arn:aws:s3:my-bucket",
                "name": "my-bucket",
                "resource_type": StagedResourceType.CLOUD_INFRA,
                "monitor_config_id": other_monitor,
                "service": "s3",
                "location": "us-east-1",
                "cloud_account_id": "123456789012",
                "source_id": "arn:aws:s3:my-bucket",  # same source_id, different monitor
            },
        )
        assert resource.monitor_config_id == other_monitor
        db.delete(resource)
