import logging
from typing import Any, Dict

from fideslib.db.base_class import Base, FidesBase
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

    def update(self, db: Session, data: Dict[str, Any]) -> FidesBase:
        """
        Updates a registration with the keys provided in `data`.
        """
        for key, value in data.items():
            setattr(self, key, value)

        return self.save(db=db)

    @classmethod
    def create_or_update(cls, db: Session, *, data: Dict[str, Any]) -> FidesBase:
        """
        Creates a registration if none exists, or updates an existing
        registration matched by `analytics_id`.
        """
        existing_model = cls.get_by(
            db=db,
            field="analytics_id",
            value=data["analytics_id"],
        )
        if existing_model:
            return existing_model.update(db=db, data=data)

        return cls.create(db=db, data=data)
