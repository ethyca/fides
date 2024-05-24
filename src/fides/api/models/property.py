# pylint: disable=protected-access
from __future__ import annotations

import random
import string
from typing import TYPE_CHECKING, Any, Dict, List, Type
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, Boolean, Text, Index, UniqueConstraint, and_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import RelationshipProperty, Session, relationship

from fides.api.db.base_class import Base
from fides.api.db.util import EnumColumn
from fides.api.schemas.property import PropertyType
from fides.config import get_config

# Hack to avoid circular dependency errors
if TYPE_CHECKING:
    from fides.api.models.privacy_experience import PrivacyExperienceConfig
    from fides.api.models.messaging_template import MessagingTemplate

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
    # Right now, we use server default to write this val.
    # In the future we may allow ability to configure which property is the default
    is_default = Column(Boolean, server_default="f", default=False)
    name = Column(String, nullable=False, unique=True)
    type = Column(EnumColumn(PropertyType), nullable=False)
    privacy_center_config = Column(MutableDict.as_mutable(JSONB), nullable=True)
    stylesheet = Column(Text, nullable=True)

    _property_paths: RelationshipProperty[List[PropertyPath]] = relationship(
        "PropertyPath",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    paths: List[str] = association_proxy("_property_paths", "path")

    experiences: RelationshipProperty[List[PrivacyExperienceConfig]] = relationship(
        "PrivacyExperienceConfig",
        secondary="plus_privacy_experience_config_property",
        back_populates="properties",
        lazy="selectin",
    )

    # todo- do I need to manually insert messaging_templates here or will DB handle it?
    messaging_templates: RelationshipProperty[List[MessagingTemplate]] = relationship(
        "MessagingTemplate",
        secondary="messaging_template_to_property",
        back_populates="properties",
        lazy="selectin",
        foreign_keys=[id],
        primaryjoin="foreign(MessagingTemplateToProperty.property_id)==any_(Property.id)",
    )

    # Only 1 property can be the default
    __table_args__ = (
        Index(
            "only_one_default",
            is_default,
            unique=True,
            postgresql_where=is_default,
        ),
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
        paths = data.pop("paths", None) or []

        matching_paths = PropertyPath.filter(
            db=db, conditions=(PropertyPath.path.in_(paths))
        ).all()
        if matching_paths:
            raise ValueError(
                f'The path(s) \'{", ".join([matching_path.path for matching_path in matching_paths])}\' are already associated with another property.'
            )

        # Ensure that there is at least 1 default. Relevant for new Fides users who have no properties at all.
        has_default_property = Property.get_by(db=db, field="is_default", value=True)
        if not has_default_property:
            data["is_default"] = True

        prop: Property = super().create(db=db, data=data, check_name=check_name)
        link_experience_configs_to_property(
            db, experience_configs=experiences, prop=prop
        )

        property_paths = [
            PropertyPath(property_id=prop.id, path=path) for path in set(paths)  # type: ignore
        ]
        prop._property_paths = property_paths

        return cls.persist_obj(db, prop)

    def update(self, db: Session, *, data: Dict[str, Any]) -> Property:
        experiences = data.pop("experiences", [])
        paths = data.pop("paths", None) or []

        matching_paths = (
            db.query(PropertyPath)
            .filter(
                and_(PropertyPath.path.in_(paths), PropertyPath.property_id != self.id)
            )
            .all()
        )
        if matching_paths:
            raise ValueError(
                f'The path(s) \'{", ".join([matching_path.path for matching_path in matching_paths])}\' are already associated with another property.'
            )

        # Ensure that there is at least 1 default. Relevent if we somehow reach a state where there is no defualt property
        has_default_property = Property.get_by(db=db, field="is_default", value=True)
        if not has_default_property:
            data["is_default"] = True

        super().update(db=db, data=data)
        link_experience_configs_to_property(
            db, experience_configs=experiences, prop=self
        )

        existing_paths = {path.path: path for path in self._property_paths}
        updated_paths = set(paths)

        # delete PropertyPath instances that are not in the updated paths
        for path in set(existing_paths.keys()) - updated_paths:
            db.delete(existing_paths[path])

        # create new PropertyPath instances for paths that don't exist
        for path in updated_paths - set(existing_paths.keys()):
            self._property_paths.append(PropertyPath(property_id=self.id, path=path))

        self.save(db)
        return self


class PropertyPath(Base):
    """Table mapping url paths to properties"""

    @declared_attr
    def __tablename__(self) -> str:
        return "plus_property_path"

    property_id = Column(
        String,
        ForeignKey("plus_property.id"),
        index=True,
        nullable=False,
        primary_key=True,
        unique=False,
    )
    path = Column(String, index=True, nullable=False, unique=True)


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


class MessagingTemplateToProperty(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "messaging_template_to_property"

    messaging_template_id = Column(
        String,
        ForeignKey("messaging_template.id"),
        unique=False,
        index=True,
        nullable=False,
        primary_key=True,
    )
    property_id = Column(
        String,
        # How to add constraint where if you try to delete a property that exists here, it throws a DB err
        ForeignKey("plus_property.id"),
        unique=False,
        index=True,
        nullable=False,
        primary_key=True,
    )
    # This inheritance allows us to enforce a unique constraint that depends on this column
    is_enabled = Column(None, ForeignKey('messaging_template.is_enabled'), primary_key=False)

    # Only 1 row allowed with the same template and property if template is enabled
    # FIXME- This is not working. I added an is_enabled column because this is required to determine the unique
    # constraint below. But because this column is a ForeignKey, SQLAlchemy is complaining
    # about not being able to determine the relationship between tables. I've tried to define
    # foreign_keys and primaryjoin args on Property / MessagingTemplate tables to set up this linkage, but
    # may have to resort to using CRUD logic to validate uniqueness here.
    __table_args__ = (
        Index(
            "only_one_overlapping_enabled_template_and_property",
            "messaging_template_id",
            "property_id",
            unique=True,
            postgresql_where=(~is_enabled)
        ),
    )
