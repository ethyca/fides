from __future__ import annotations

from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr

from fides.api.models.detection_discovery.core import StagedResourceBase


class CloudInfraStagedResource(StagedResourceBase):
    """
    Staged resource model for cloud infrastructure resources.

    Concrete subclass of StagedResourceBase with its own dedicated table.
    See CloudInfraResourceMetadata in fidesplus for the shape of the meta field.
    """

    @declared_attr
    def __tablename__(self) -> str:  # type: ignore[override]
        return "cloud_infra_staged_resource"

    __table_args__ = (
        UniqueConstraint(
            "monitor_config_id",
            "source_id",
            name="uq_cloud_infra_monitor_config_id_source_id",
        ),
    )

    service = Column(String, nullable=False)  # e.g. "s3", "rds"
    tags = Column(JSONB, nullable=True)  # cloud resource tags/labels
    location = Column(
        String, nullable=False, index=True
    )  # region/zone, e.g. "us-east-1"
    cloud_account_id = Column(
        String, nullable=False, index=True
    )  # AWS account ID / Azure subscription ID / GCP project ID
    source_id = Column(
        String, nullable=False
    )  # provider-specific resource identifier (e.g. AWS ARN)
