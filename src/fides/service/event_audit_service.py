"""Service for creating and managing event audit records."""

from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.event_audit import EventAudit, EventAuditStatus, EventAuditType
from fides.api.request_context import get_user_id


class EventAuditService:
    """Service for creating and managing event audit records."""

    def __init__(self, db: Session):
        self.db = db

    def create_event_audit(
        self,
        event_type: EventAuditType,
        status: EventAuditStatus,
        *,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_identifier: Optional[str] = None,
        description: Optional[str] = None,
        event_details: Optional[Dict[str, Any]] = None,
    ) -> EventAudit:
        """Create a new audit event record."""

        # Uses the passed in user_id or falls back to the authenticated user via get_user_id()
        data = {
            "event_type": event_type,
            "status": status,
            "user_id": user_id or get_user_id(),
            "resource_type": resource_type,
            "resource_identifier": resource_identifier,
            "description": description,
            "event_details": event_details,
        }
        event_audit = EventAudit.create(
            db=self.db,
            data=data,
        )

        msg_payload = {**data}
        msg_payload.pop("event_type")
        msg_payload["status"] = status.value
        msg = f"Created event audit {event_type} for resource: {resource_type}. {msg_payload}"

        logger.info(msg)

        return event_audit

    def get_events_for_resource(
        self,
        resource_type: str,
        resource_identifier: Optional[str] = None,
        limit: int = 100,
    ) -> List[EventAudit]:
        """Get audit events for a specific resource."""

        query = self.db.query(EventAudit).filter(
            EventAudit.resource_type == resource_type
        )

        if resource_identifier:
            query = query.filter(EventAudit.resource_identifier == resource_identifier)

        return query.order_by(EventAudit.created_at.desc()).limit(limit).all()

    def get_events_by_user(self, user_id: str, limit: int = 100) -> List[EventAudit]:
        """Get audit events by a specific user."""

        return (
            self.db.query(EventAudit)
            .filter(EventAudit.user_id == user_id)
            .order_by(EventAudit.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_events_by_type(
        self, event_type: EventAuditType, limit: int = 100
    ) -> List[EventAudit]:
        """Get audit events of a specific type."""

        return (
            self.db.query(EventAudit)
            .filter(EventAudit.event_type == event_type)
            .order_by(EventAudit.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_events_by_category(
        self, category_prefix: str, limit: int = 100
    ) -> List[EventAudit]:
        """Get all events matching a category prefix (e.g., 'consent', 'system', 'taxonomy')."""

        prefix_with_dot = category_prefix + "."

        return (
            self.db.query(EventAudit)
            .filter(EventAudit.event_type.startswith(prefix_with_dot))
            .order_by(EventAudit.created_at.desc())
            .limit(limit)
            .all()
        )
