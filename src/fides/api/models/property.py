from __future__ import annotations

import random
import string
from typing import TYPE_CHECKING, Any, Dict, List, Type
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import RelationshipProperty, Session, relationship

from fides.api.db.base_class import Base
from fides.api.db.util import EnumColumn
from fides.api.schemas.property import PropertyType
from fides.config import get_config

if TYPE_CHECKING:
    from fides.api.models.privacy_experience import PrivacyExperienceConfig

CONFIG = get_config()


class Property(Base):
    """
    This class serves as a model for digital properties, such as websites or other online platforms.
    """

    def generate_id(self) -> str:
        """
        Generate a unique ID in the format 'FDS-XXXXXX' using uppercase alphanumeric characters.
        """
        characters = string.ascii_uppercase + string.digits
        return "FDS-" + "".join(random.choices(characters, k=6))

    @declared_attr
    def __tablename__(self) -> str:
        return "plus_property"

    id = Column(
        String,
        primary_key=True,
        default=generate_id,
    )
    name = Column(String, nullable=False, unique=True)
    type = Column(EnumColumn(PropertyType), nullable=False)

    experiences: RelationshipProperty[List[PrivacyExperienceConfig]] = relationship(
        "PrivacyExperienceConfig",
        secondary="plus_privacy_experience_config_property",
        back_populates="properties",
        lazy="selectin",
    )

    @classmethod
    def create(
        cls: Type[Property],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = True,
    ) -> Property:
        experiences = data.pop("experiences", [])
        prop: Property = super().create(db=db, data=data, check_name=check_name)
        link_experience_configs_to_property(
            db, experience_configs=experiences, prop=prop
        )
        return prop

    def update(self, db: Session, *, data: Dict[str, Any]) -> Property:
        experiences = data.pop("experiences", [])
        super().update(db=db, data=data)
        link_experience_configs_to_property(
            db, experience_configs=experiences, prop=self
        )
        return self


class PrivacyExperienceConfigProperty(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "plus_privacy_experience_config_property"

    def generate_uuid(self) -> str:
        """
        Generates a uuid with a prefix based on the tablename to be used as the
        record's ID value
        """
        try:
            prefix = f"{self.current_column.table.name[:3]}_"  # type: ignore
        except AttributeError:
            prefix = ""
        uuid = str(uuid4())
        return f"{prefix}{uuid}"

    # Overrides Base.id so this is not a primary key.
    # Instead, we have a composite PK of privacy_experience_config_id and property_id
    id = Column(String(255), default=generate_uuid)

    privacy_experience_config_id = Column(
        String,
        ForeignKey("privacyexperienceconfig.id"),
        index=True,
        nullable=False,
        primary_key=True,
    )
    property_id = Column(
        String,
        ForeignKey("plus_property.id"),
        index=True,
        nullable=False,
        primary_key=True,
    )


def link_experience_configs_to_property(
    db: Session,
    *,
    experience_configs: List[Dict[str, Any]],
    prop: Property,
) -> List[PrivacyExperienceConfig]:
    """
    Link supplied experience configs to the property.
    """

    # delayed import to avoid circular declarations
    from fides.api.models.privacy_experience import PrivacyExperienceConfig

    if experience_configs:
        experience_config_ids = [
            experience_config["id"] for experience_config in experience_configs
        ]
        new_experience_configs = (
            db.query(PrivacyExperienceConfig)
            .filter(PrivacyExperienceConfig.id.in_(experience_config_ids))
            .all()
        )
        prop.experiences = new_experience_configs
    else:
        prop.experiences = []

    prop.save(db)
    return prop.experiences
