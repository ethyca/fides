from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import (
    BOOLEAN,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import RelationshipProperty, Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.sql_models import FidesBase  # type: ignore[attr-defined]


class TargetType(str, Enum):
    """Enumeration of target types that taxonomies can apply to."""

    SYSTEM = "system"
    DATASET = "dataset"
    COLLECTION = "collection"
    FIELD = "field"
    PRIVACY_DECLARATION = "privacy_declaration"
    TAXONOMY = "taxonomy"  # For taxonomy-to-taxonomy relationships


class Taxonomy(Base, FidesBase):
    """The SQL model for taxonomy resources."""

    _allowed_usages: RelationshipProperty[List[TaxonomyAllowedUsage]] = relationship(
        "TaxonomyAllowedUsage",
        back_populates="source_taxonomy",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Association proxy to simplify access to target_type values
    # This allows getting a list of strings while the actual storage
    # is handled through the TaxonomyAllowedUsage model
    # Updates should be done through the create/update methods
    applies_to: List[str] = association_proxy("_allowed_usages", "target_type")

    @classmethod
    def create(
        cls: Type["Taxonomy"],
        db: Session,
        *,
        data: Dict[str, Any],
        check_name: bool = True,
    ) -> "Taxonomy":
        """Create a new Taxonomy with proper handling of applies_to."""
        applies_to = data.pop("applies_to", [])

        # Create the taxonomy
        taxonomy: Taxonomy = super().create(db=db, data=data, check_name=check_name)

        # Create TaxonomyAllowedUsage objects for each applies_to value
        allowed_usages = [
            TaxonomyAllowedUsage(  # type: ignore
                source_taxonomy_key=taxonomy.fides_key, target_type=target_type
            )
            for target_type in set(applies_to)
        ]
        taxonomy._allowed_usages = allowed_usages  # pylint: disable=protected-access

        return cls.persist_obj(db, taxonomy)

    def update(self, db: Session, *, data: Dict[str, Any]) -> "Taxonomy":
        """Update a Taxonomy with proper handling of applies_to."""
        applies_to = data.pop("applies_to", None)

        # Update the base fields
        super().update(db=db, data=data)

        # If applies_to was provided, update it
        if applies_to is not None:
            existing_usages = {
                usage.target_type: usage for usage in self._allowed_usages
            }
            updated_types = set(applies_to)

            # Delete TaxonomyAllowedUsage instances that are not in the updated list
            for target_type in set(existing_usages.keys()) - updated_types:
                db.delete(existing_usages[target_type])

            # Create new TaxonomyAllowedUsage instances for types that don't exist
            for target_type in updated_types - set(existing_usages.keys()):
                self._allowed_usages.append(
                    TaxonomyAllowedUsage(  # type: ignore
                        source_taxonomy_key=self.fides_key, target_type=target_type
                    )
                )

        return self


class TaxonomyAllowedUsage(Base):
    """
    The SQL model for taxonomy allowed usage.
    Defines what types of targets a taxonomy can be applied to.

    target_type can be either:
    - A generic type: "system", "dataset", "field", "collection", "privacy_declaration"
    - A taxonomy key: "data_categories", "data_uses", etc.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "taxonomy_allowed_usage"

    source_taxonomy: RelationshipProperty[Taxonomy] = relationship(
        "Taxonomy",
        back_populates="_allowed_usages",
    )

    source_taxonomy_key = Column(
        String,
        ForeignKey("taxonomy.fides_key", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    target_type = Column(
        String, primary_key=True
    )  # Can be "system", "dataset", OR a taxonomy key like "data_categories"

    __table_args__ = (
        # Simple two-column index for queries
        Index("ix_allowed_usage_lookup", "source_taxonomy_key", "target_type"),
    )


class TaxonomyElement(Base, FidesBase):
    """
    The SQL model for taxonomy elements.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "taxonomy_element"

    # Which taxonomy this element belongs to
    taxonomy_type = Column(
        String,
        ForeignKey("taxonomy.fides_key", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    parent_key = Column(
        Text, ForeignKey("taxonomy_element.fides_key", ondelete="RESTRICT"), index=True
    )
    active = Column(BOOLEAN, default=True, nullable=False, index=True)

    children: RelationshipProperty[List[TaxonomyElement]] = relationship(
        "TaxonomyElement",
        back_populates="parent",
        cascade="save-update, merge, refresh-expire",  # intentionally do not cascade deletes
        passive_deletes="all",
    )

    parent: RelationshipProperty[Optional[TaxonomyElement]] = relationship(
        "TaxonomyElement",
        back_populates="children",
        remote_side="TaxonomyElement.fides_key",
    )


class TaxonomyUsage(Base):
    """
    The SQL model for taxonomy usage.
    Tracks the application of taxonomy elements to other taxonomy elements.

    Example: Applying a "high" tag (from risk taxonomy) to
             "user.contact.email" (from data_categories taxonomy).
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "taxonomy_usage"

    # The taxonomy element being applied (e.g., risk)
    source_element_key = Column(
        String,
        ForeignKey(
            "taxonomy_element.fides_key",
            ondelete="CASCADE",
            name="fk_taxonomy_usage_source_element",
        ),
        nullable=False,
        index=True,
    )

    # The taxonomy element it's being applied to (e.g., a data category)
    target_element_key = Column(
        String,
        ForeignKey(
            "taxonomy_element.fides_key",
            ondelete="CASCADE",
            name="fk_taxonomy_usage_target_element",
        ),
        nullable=False,
        index=True,
    )

    # Denormalized taxonomy types for validation and performance
    source_taxonomy = Column(String, nullable=False, index=True)
    target_taxonomy = Column(String, nullable=False, index=True)

    # Relationships for easier access
    source_element: RelationshipProperty[TaxonomyElement] = relationship(
        "TaxonomyElement",
        foreign_keys=[source_element_key],
        backref="usages_as_source",
    )

    target_element: RelationshipProperty[TaxonomyElement] = relationship(
        "TaxonomyElement",
        foreign_keys=[target_element_key],
        backref="usages_as_target",
    )

    __table_args__ = (
        # Validate that this type of usage is allowed
        ForeignKeyConstraint(
            ["source_taxonomy", "target_taxonomy"],
            [
                "taxonomy_allowed_usage.source_taxonomy_key",
                "taxonomy_allowed_usage.target_type",
            ],
            ondelete="RESTRICT",
            name="fk_taxonomy_usage_allowed",
        ),
        # Prevent duplicate applications
        UniqueConstraint(
            "source_element_key",
            "target_element_key",
            name="uq_taxonomy_usage",
        ),
        # Index for finding all usages by taxonomy combination
        Index("ix_taxonomy_usage_by_taxonomies", "source_taxonomy", "target_taxonomy"),
    )
