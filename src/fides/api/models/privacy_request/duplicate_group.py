import hashlib
import json
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Column, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base  # type: ignore[attr-defined]
from fides.config.duplicate_detection_settings import DuplicateDetectionSettings

if TYPE_CHECKING:
    from fides.api.models.privacy_request.privacy_request import PrivacyRequest


def generate_deterministic_uuid(rule_version: str, dedup_key: str) -> uuid.UUID:
    """Overrides the base class method to generate a deterministic group id.

    The actual rule version is a hash of the duplicate detection settings config,
    using simple examples here for illustration:
    - under rule "email", duplicate@example.com → group A,
    - under rule "email|phone", duplicate@example.com|1234567890 → group B.
    - ... and so on.

    No collisions, no overlap.
    """
    # Combine the rule version and the key into a stable hash
    hash_input = f"{rule_version}:{dedup_key}".encode("utf-8")
    return uuid.UUID(hashlib.md5(hash_input).hexdigest())


def generate_rule_version(config: DuplicateDetectionSettings) -> str:
    """Generate a stable short hash for the dedup rule config."""
    normalized = json.dumps(config.model_dump(), sort_keys=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8]


class DuplicateGroup(Base):
    """
    A table for storing duplicate request group information.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "duplicate_group"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_version = Column(Text, nullable=False)
    # TODO: The is_active column is not used yet since we are defaulting to just email for
    # duplicate detection. When we allow users to configure the duplicate detection settings,
    # we will need to add a way to activate/deactivate duplicate groups.
    # This should be done by getting the previous rule version and deactivating all groups with
    # that rule version. New groups will be created with the new rule version.
    is_active = Column(Boolean, default=True, nullable=False)
    dedup_key = Column(Text, nullable=False)
    privacy_requests = relationship(
        "PrivacyRequest",
        back_populates="duplicate_group",
        lazy="dynamic",
        primaryjoin="and_(DuplicateGroup.id == PrivacyRequest.duplicate_request_group_id)",
    )

    @classmethod
    def create(
        cls, db: Session, *, data: dict[str, Any], check_name: bool = False
    ) -> "DuplicateGroup":
        """Create a new duplicate group.
        Override the base class method to generate a deterministic group id.
        If the group already exists, update the is_active column to True and return the group.
        """
        group_id = generate_deterministic_uuid(data["rule_version"], data["dedup_key"])
        # If the group already exists, update the is_active column to True and return the group
        duplicate_group = (
            db.query(DuplicateGroup).filter(DuplicateGroup.id == group_id).one_or_none()
        )
        if duplicate_group:
            duplicate_group.update(db, data={"is_active": True})
            return duplicate_group

        # If the group does not exist, create a new one
        data["id"] = group_id
        return super().create(db, data=data, check_name=check_name)
