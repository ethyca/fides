# pylint: disable=R0401, C0302

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base  # type: ignore[attr-defined]
from fides.api.db.util import EnumColumn
from fides.api.models.privacy_request.custom_field_persistence import (
    CustomPrivacyRequestFieldPersistenceMixin,
)
from fides.api.models.privacy_request.provided_identity import ProvidedIdentity
from fides.api.schemas.privacy_request import PrivacyRequestSource
from fides.api.schemas.redis_cache import IdentityBase
from fides.api.util.identity_verification import IdentityVerificationMixin

if TYPE_CHECKING:
    from fides.api.models.privacy_request.privacy_request import (
        PrivacyRequest,  # type: ignore[attr-defined]
    )


class Consent(Base):
    """The DB ORM model for Consent."""

    provided_identity_id = Column(
        String,
        ForeignKey(ProvidedIdentity.id),
        nullable=False,
    )
    data_use = Column(String, nullable=False)
    data_use_description = Column(String)
    opt_in = Column(Boolean, nullable=False)
    has_gpc_flag = Column(
        Boolean,
        server_default="f",
        default=False,
        nullable=False,
    )
    conflicts_with_gpc = Column(
        Boolean,
        server_default="f",
        default=False,
        nullable=False,
    )

    provided_identity = relationship(ProvidedIdentity, back_populates="consent")

    UniqueConstraint(provided_identity_id, data_use, name="uix_identity_data_use")

    identity: Optional[IdentityBase] = None


class ConsentRequest(
    CustomPrivacyRequestFieldPersistenceMixin, IdentityVerificationMixin, Base
):
    """Tracks consent requests."""

    _custom_field_fk_column = "consent_request_id"

    property_id = Column(
        String,
        nullable=True,
    )
    provided_identity_id = Column(
        String, ForeignKey(ProvidedIdentity.id), nullable=False
    )
    provided_identity = relationship(
        ProvidedIdentity,
        back_populates="consent_request",
    )

    custom_fields = relationship(
        "CustomPrivacyRequestField", back_populates="consent_request"
    )

    preferences = Column(
        MutableList.as_mutable(JSONB),
        nullable=True,
    )

    identity_verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    source = Column(EnumColumn(PrivacyRequestSource), nullable=True)

    privacy_request_id = Column(String, ForeignKey("privacyrequest.id"), nullable=True)
    privacy_request = relationship("PrivacyRequest")

    def verify_identity(
        self,
        db: Session,
        provided_code: Optional[str] = None,
    ) -> None:
        """
        A method to call the internal identity verification method provided by the
        `IdentityVerificationMixin`.
        """
        self._verify_identity(provided_code=provided_code)
        self.identity_verified_at = datetime.utcnow()
        self.save(db)

    def get_persisted_custom_privacy_request_fields(self) -> Dict[str, Any]:
        return {
            field.field_name: {
                "label": field.field_label,
                "value": field.encrypted_value["value"],
            }
            for field in self.custom_fields  # type: ignore[attr-defined]
        }
