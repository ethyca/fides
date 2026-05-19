from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict

from fides.api.db.base_class import Base  # type: ignore[attr-defined]


class AccessPackageReview(Base):
    """Stores review state for an access package: redactions applied by an admin
    and approval metadata. One-to-one with PrivacyRequest.

    Row lifecycle:
    - Created when a privacy request enters the ``awaiting_access_review`` state.
    - Updated via PUT /redactions (writes ``redactions``) and POST /approve
      (sets ``approved_at`` / ``approved_by``).
    - Deleted on reprocess: CASCADE from PrivacyRequest delete, or explicit
      cleanup callback on restart.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "access_package_review"

    privacy_request_id = Column(
        String,
        ForeignKey("privacyrequest.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    redactions = Column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        server_default="{}",
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String, nullable=True)
