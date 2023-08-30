"""Tasks that represent units of work for Privacy Requests."""
from __future__ import annotations

from sqlalchemy import ARRAY, Column
from sqlalchemy import (
    ForeignKey,
    String,
)
from sqlalchemy.sql.sqltypes import String

from fides.api.db.base_class import Base
from fides.api.models.privacy_request import PrivacyRequest


class Task(Base):
    """
    The SQL model for a Task.

    Note: There is a composite key of 'target_field' + 'privacy_request_id'. Since a
    node should not be visited more than once this is considered safe.
    """

    __tablename__ = "tasks"

    # The field that is targeted by this task
    target_field = Column(String, primary_key=True, nullable=False)

    # The PrivacyRequest this task belongs to
    privacy_request_id = Column(
        String,
        ForeignKey(PrivacyRequest.id),
        nullable=False,
        primary_key=True,
    )
    # The task(s) that rely on this task's completion
    downstream = Column(ARRAY(String))

    # The task(s) that this task relies on
    upstream = Column(ARRAY(String))

    # The data
    result_data = Column(String)

    # The ConnectionConfig used to access the target_field
    connection_config = Column(String)

    # Additional Metadata
    labels = Column(ARRAY(String))
