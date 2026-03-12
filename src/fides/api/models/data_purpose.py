from typing import Any, Type

from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session

from fides.api.common_exceptions import KeyOrNameAlreadyExists
from fides.api.db.base_class import Base
from fides.api.models.sql_models import FidesBase


class DataPurpose(Base, FidesBase):
    """
    A standalone, reusable declaration of why data is processed.

    Replaces the system-bound PrivacyDeclaration with a centrally-governed
    entity. Flat (no hierarchy) but inherits FidesBase for fides_key, name,
    description, organization_fides_key, and tags.
    """

    __tablename__ = "data_purpose"

    data_use = Column(String, nullable=False, index=True)
    data_subject = Column(String, nullable=True)
    data_categories = Column(ARRAY(String), server_default="{}", nullable=False)
    legal_basis_for_processing = Column(String, nullable=True)
    flexible_legal_basis_for_processing = Column(
        Boolean, server_default="t", nullable=False
    )
    special_category_legal_basis = Column(String, nullable=True)
    impact_assessment_location = Column(String, nullable=True)
    retention_period = Column(String, nullable=True)
    features = Column(ARRAY(String), server_default="{}", nullable=False)

    @classmethod
    def create(
        cls: Type["DataPurpose"],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> "DataPurpose":
        """Override create to enforce fides_key uniqueness and skip name uniqueness check.

        DataPurpose uses fides_key for uniqueness, not name.
        """
        if "fides_key" in data and data["fides_key"]:
            existing = db.query(cls).filter(cls.fides_key == data["fides_key"]).first()
            if existing:
                raise KeyOrNameAlreadyExists(
                    f'DataPurpose with fides_key "{data["fides_key"]}" already exists.'
                )
        return super().create(db=db, data=data, check_name=False)
