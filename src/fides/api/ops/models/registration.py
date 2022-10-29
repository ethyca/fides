import logging
from typing import Any, Dict

from fideslib.db.base_class import Base, FidesBase
from sqlalchemy import (
    Boolean,
    Column,
    String,
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class UserRegistration(Base):
    """
    Stores registration status of a particular Fides deployment.
    """

    user_email = Column(String, nullable=True)
    user_organization = Column(String, nullable=True)
    analytics_id = Column(String, unique=True, nullable=False)
    opt_in = Column(Boolean, nullable=False, default=False)

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
            existing_model.opt_in = data["opt_in"]
            return existing_model.save(db=db)

        return cls.create(db=db, data=data)
