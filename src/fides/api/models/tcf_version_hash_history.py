from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB as jsonb
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func

from fides.api.db.base_class import Base


class TCFVersionHashTriggerSource(str, Enum):
    experience_config_update = "experience_config_update"
    experience_config_limited_update = "experience_config_limited_update"
    experience_serve_uncached = "experience_serve_uncached"
    compass_sync = "compass_sync"
    tcf_configuration_delete = "tcf_configuration_delete"
    tcf_publisher_restriction_create = "tcf_publisher_restriction_create"
    tcf_publisher_restriction_update = "tcf_publisher_restriction_update"
    tcf_publisher_restriction_delete = "tcf_publisher_restriction_delete"
    unknown = "unknown"


class TCFVersionHashHistory(Base):
    """Records each transition of the TCF version hash for each experience config, enabling audit of when consent re-collection is required."""

    @declared_attr
    def __tablename__(self) -> str:
        return "tcf_version_hash_history"

    privacy_experience_config_id = Column(
        String(255),
        ForeignKey("privacyexperienceconfig.id", ondelete="CASCADE"),
        index=True,
    )
    previous_hash = Column(String, nullable=True)
    current_hash = Column(String, nullable=False, index=True)
    changed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    trigger_source = Column(String, nullable=False)
    details = Column(jsonb, nullable=True)
