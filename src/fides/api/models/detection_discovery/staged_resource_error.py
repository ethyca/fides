"""Module for staged resource error tracking."""

from sqlalchemy import Column, DateTime, ForeignKey, String

from fides.api.db.base_class import Base, FidesBase


class StagedResourceError(Base):
    """
    DB model for tracking errors associated with staged resources.
    Linked to StagedResource via FK with cascade delete.
    """

    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)
    staged_resource_urn = Column(
        String,
        ForeignKey("stagedresource.urn", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    error_type = Column(String, nullable=False)
    diff_status = Column(String, nullable=False)  # Phase where error occurred
    task_id = Column(String, nullable=True, index=True)
