# pylint: disable=R0401, C0302

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from loguru import logger
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base  # type: ignore[attr-defined]
from fides.api.db.util import EnumColumn
from fides.api.models.privacy_request.privacy_request import CustomPrivacyRequestField
from fides.api.models.privacy_request.provided_identity import ProvidedIdentity
from fides.api.schemas.privacy_request import PrivacyRequestSource
from fides.api.schemas.redis_cache import (
    CustomPrivacyRequestField as CustomPrivacyRequestFieldSchema,
)
from fides.api.schemas.redis_cache import IdentityBase
from fides.api.util.cache import FidesopsRedis, get_cache
from fides.api.util.identity_verification import IdentityVerificationMixin
from fides.config import CONFIG

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


class ConsentRequest(IdentityVerificationMixin, Base):
    """Tracks consent requests."""

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

    def get_cached_identity_data(self) -> Dict[str, Any]:
        """Retrieves any identity data pertaining to this request from the cache."""
        prefix = f"id-{self.id}-identity-*"
        cache: FidesopsRedis = get_cache()
        keys = cache.keys(prefix)
        return {key.split("-")[-1]: cache.get(key) for key in keys}

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

    def persist_custom_privacy_request_fields(
        self,
        db: Session,
        custom_privacy_request_fields: Optional[
            Dict[str, CustomPrivacyRequestFieldSchema]
        ],
    ) -> None:
        if not custom_privacy_request_fields:
            return

        if CONFIG.execution.allow_custom_privacy_request_field_collection:
            for key, item in custom_privacy_request_fields.items():
                if item.value:
                    hashed_value = CustomPrivacyRequestField.hash_value(item.value)
                    CustomPrivacyRequestField.create(
                        db=db,
                        data={
                            "consent_request_id": self.id,
                            "field_name": key,
                            "field_label": item.label,
                            "encrypted_value": {"value": item.value},
                            "hashed_value": hashed_value,
                        },
                    )
        else:
            logger.info(
                "Custom fields provided in consent request {}, but config setting 'CONFIG.execution.allow_custom_privacy_request_field_collection' prevents their storage.",
                self.id,
            )

    def get_persisted_custom_privacy_request_fields(self) -> Dict[str, Any]:
        return {
            field.field_name: {
                "label": field.field_label,
                "value": field.encrypted_value["value"],
            }
            for field in self.custom_fields  # type: ignore[attr-defined]
        }
