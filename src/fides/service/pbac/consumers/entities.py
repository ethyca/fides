from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from fides.service.pbac.purposes.entities import DataPurposeEntity

if TYPE_CHECKING:
    from fides.api.models.data_consumer import DataConsumer
    from fides.api.models.sql_models import System  # type: ignore[attr-defined]


@dataclass
class DataConsumerEntity:
    """Unified domain entity for both DataConsumer rows and System-as-consumer."""

    id: str
    name: str
    type: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    external_id: Optional[str] = None
    purposes: list[DataPurposeEntity] = field(default_factory=list)
    purpose_fides_keys: list[str] = field(default_factory=list)
    system_fides_key: Optional[str] = None
    vendor_id: Optional[str] = None
    egress: Optional[dict[str, Any]] = None
    ingress: Optional[dict[str, Any]] = None
    data_shared_with_third_parties: Optional[bool] = None
    third_parties: Optional[str] = None
    shared_categories: Optional[list[str]] = None
    tags: list[str] = field(default_factory=list)
    contact_email: Optional[str] = None
    contact_slack_channel: Optional[str] = None
    contact_details: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        # Store purpose references as fides_keys only (not nested entities)
        d["purpose_fides_keys"] = self.purpose_fides_keys
        del d["purposes"]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> DataConsumerEntity:
        d = dict(d)
        d["created_at"] = datetime.fromisoformat(d["created_at"])
        d["updated_at"] = datetime.fromisoformat(d["updated_at"])
        d.setdefault("purpose_fides_keys", [])
        d.setdefault("purposes", [])
        return cls(**d)

    @classmethod
    def from_consumer(cls, obj: DataConsumer) -> DataConsumerEntity:
        purposes = [
            DataPurposeEntity.from_orm(cp.data_purpose) for cp in obj.consumer_purposes
        ]
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            type=obj.type,
            external_id=obj.external_id,
            purposes=purposes,
            purpose_fides_keys=[p.fides_key for p in purposes],
            egress=obj.egress,
            ingress=obj.ingress,
            data_shared_with_third_parties=obj.data_shared_with_third_parties,
            third_parties=obj.third_parties,
            shared_categories=obj.shared_categories or [],
            tags=obj.tags or [],
            contact_email=obj.contact_email,
            contact_slack_channel=obj.contact_slack_channel,
            contact_details=obj.contact_details,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    @classmethod
    def from_system(cls, obj: System) -> DataConsumerEntity:
        purposes = [
            DataPurposeEntity.from_orm(sp.data_purpose) for sp in obj.system_purposes
        ]
        return cls(
            id=obj.id,
            name=obj.name or obj.fides_key,
            description=obj.description,
            type="system",
            purposes=purposes,
            purpose_fides_keys=[p.fides_key for p in purposes],
            system_fides_key=obj.fides_key,
            vendor_id=getattr(obj, "vendor_id", None),
            egress=obj.egress if isinstance(obj.egress, dict) else None,
            ingress=obj.ingress if isinstance(obj.ingress, dict) else None,
            tags=obj.tags or [],
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
