"""Model for tracking Jira ticket state linked to ManualTaskInstance records.

Each JiraTicketTask has a 1:1 relationship with a ManualTaskInstance and
stores Jira-specific fields (ticket key, URL, external status) that the
polling service uses to track ticket lifecycle.
"""

from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base


class JiraTicketTask(Base):
    """Tracks a Jira ticket linked to a ManualTaskInstance.

    Created when a Jira ticket is opened for a privacy request.  The polling
    service queries open records (external_status_category != 'done') and
    updates them from the Jira API.
    """

    __tablename__ = "jira_ticket_task"

    manual_task_instance_id = Column(
        String,
        ForeignKey("manual_task_instance.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    connection_config_id = Column(
        String,
        ForeignKey("connectionconfig.id", ondelete="CASCADE"),
        nullable=False,
    )

    ticket_key = Column(String, nullable=True)
    ticket_url = Column(String, nullable=True)
    external_status = Column(String, nullable=True)
    external_status_category = Column(String, nullable=True)
    last_polled_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_jira_ticket_task_open",
            "external_status_category",
            postgresql_where=text(
                "external_status_category IS NULL OR external_status_category != 'done'"
            ),
        ),
        Index("ix_jira_ticket_task_connection_config_id", "connection_config_id"),
    )

    manual_task_instance = relationship(
        "ManualTaskInstance",
        backref="jira_ticket_task",
        uselist=False,
    )
    connection_config = relationship(
        "ConnectionConfig",
        backref="jira_ticket_tasks",
    )

    @classmethod
    def get_open_tasks(cls, db: Session) -> list["JiraTicketTask"]:
        """Return all tasks that still need polling (not done)."""
    @classmethod
    def get_open_tasks(cls, db: Session) -> list["JiraTicketTask"]:
        """Return all tasks that still need polling (not done)."""
        return (
            db.query(cls)
            .filter(
                (cls.external_status_category.is_(None))
                | (cls.external_status_category != DONE_STATUS_CATEGORY)
            )
            .all()
        )
            .all()
        )

    @classmethod
    def get_by_instance_id(
        cls, db: Session, instance_id: str
    ) -> Optional["JiraTicketTask"]:
        """Look up a JiraTicketTask by its ManualTaskInstance ID."""
        return db.query(cls).filter(cls.manual_task_instance_id == instance_id).first()
