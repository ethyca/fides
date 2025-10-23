"""EventAudit model and related enums for comprehensive audit logging."""

from enum import Enum as EnumType

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base
from fides.api.db.util import EnumColumn


class EventAuditType(str, EnumType):
    """Hierarchical event types for audit logging - variable depth as needed."""

    # System
    system_updated = "system.updated"

    # System group
    system_group_created = "system_group.created"
    system_group_updated = "system_group.updated"
    system_group_deleted = "system_group.deleted"

    # Taxonomy
    taxonomy_created = "taxonomy.created"
    taxonomy_updated = "taxonomy.updated"
    taxonomy_deleted = "taxonomy.deleted"
    taxonomy_usage_updated = "taxonomy.usage.updated"
    taxonomy_usage_deleted = "taxonomy.usage.deleted"
    taxonomy_element_created = "taxonomy.element.created"
    taxonomy_element_updated = "taxonomy.element.updated"
    taxonomy_element_deleted = "taxonomy.element.deleted"

    # Connection operations
    connection_created = "connection.created"
    connection_updated = "connection.updated"
    connection_deleted = "connection.deleted"

    # Connection secrets operations
    connection_secrets_created = "connection.secrets.created"
    connection_secrets_updated = "connection.secrets.updated"

    # Digest
    digest_execution_started = "digest.execution.started"
    digest_execution_completed = "digest.execution.completed"
    digest_execution_interrupted = "digest.execution.interrupted"
    digest_execution_resumed = "digest.execution.resumed"
    digest_communications_sent = "digest.communications.sent"
    digest_checkpoint_created = "digest.checkpoint.created"


class EventAuditStatus(str, EnumType):
    """Status enum for event audit logging."""

    succeeded = "succeeded"
    failed = "failed"


class EventAudit(Base):
    """Audit log for significant business events across the Fides platform."""

    @declared_attr
    def __tablename__(cls) -> str:
        return "event_audit"

    # Uses EventAuditType values but left as String to avoid future migrations
    event_type = Column(String, index=True, nullable=False)
    user_id = Column(String, nullable=True, index=True)

    # Resource information
    resource_type = Column(String, nullable=True, index=True)
    resource_identifier = Column(String, nullable=True, index=True)

    # User-friendly description of event
    description = Column(Text, nullable=True)

    # Structured data about event
    event_details = Column(JSONB, nullable=True)

    # Status of the event
    status = Column(
        EnumColumn(EventAuditStatus),
        index=True,
        nullable=False,
    )
