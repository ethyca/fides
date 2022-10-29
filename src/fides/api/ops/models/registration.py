import logging
from typing import Any, Dict, Optional, Tuple

from fideslib.db.base_class import Base, FidesBase

# TODO: Uncomment once https://github.com/ethyca/fideslog/pull/87/files#diff-2a06515c42b1c2250befd410a494c1173fbbde8dff2a07e79ea597c7a3e25994
# is merged
# from fideslog.sdk.python.registration import Registration
from sqlalchemy import (
    Boolean,
    Column,
    String,
)
from sqlalchemy.orm import Session
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
from fides.ctl.core.config import get_config

CONFIG = get_config()

logger = logging.getLogger(__name__)


class Registration:
    """
    This is a stub of the object at: https://github.com/ethyca/fideslog/pull/87/files#diff-2a06515c42b1c2250befd410a494c1173fbbde8dff2a07e79ea597c7a3e25994
    and will be replaced once the PR is merged.
    """

    def __init__(self, email: Optional[str], organization: Optional[str]) -> None:
        """
        A docstring.
        """
        self.email = email
        self.organization = organization


class UserRegistration(Base):
    """
    Stores registration status of a particular Fides deployment.
    """

    user_email = Column(
        StringEncryptedType(
            String,
            CONFIG.security.app_encryption_key,
            AesEngine,
        ),
        nullable=True,
    )
    user_organization = Column(String, nullable=True)
    analytics_id = Column(String, unique=True, nullable=False)
    opt_in = Column(Boolean, nullable=False, default=False)

    @classmethod
    def create_or_update(
        cls, db: Session, *, data: Dict[str, Any]
    ) -> Tuple[FidesBase, bool]:
        """
        Creates a registration if none exists, or updates an existing
        registration matched by `analytics_id`.
        """
        created_or_updated = True
        existing_model = cls.get_by(
            db=db,
            field="analytics_id",
            value=data["analytics_id"],
        )
        if existing_model:
            updated_model, created_or_updated = existing_model.update(db=db, data=data)
            return (updated_model, created_or_updated)

        return (cls.create(db=db, data=data), created_or_updated)

    def update(self, db: Session, data: Dict[str, Any]) -> Tuple[FidesBase, bool]:
        """
        Updates a registration with the keys provided in `data`.
        """
        model_updated = False
        for key, value in data.items():
            if getattr(self, key) != value:
                setattr(self, key, value)
                model_updated = True

        if model_updated:
            return (self.save(db=db), model_updated)

        return (self, model_updated)

    def as_fideslog(self) -> Registration:
        """
        Converts a `UserRegistration` into the format required by Fideslog.
        """
        email: Optional[str] = self.user_email
        organization: Optional[str] = self.user_organization
        return Registration(
            email=email,
            organization=organization,
        )
