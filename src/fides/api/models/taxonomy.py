from __future__ import annotations

from enum import Enum
from typing import List, Optional, Set

from sqlalchemy import (
    BOOLEAN,
    JSON,
    Column,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import RelationshipProperty, relationship

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

    @classmethod
    def generic_types(cls) -> Set[str]:
        """Returns all target types except TAXONOMY."""
        return {t.value for t in cls if t != cls.TAXONOMY}


class Taxonomy(Base, FidesBase):
    """
    The SQL model for taxonomy resources.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "taxonomy"

    # Store what this taxonomy can be applied to as JSON
    # Format: ["system", "dataset", "data_categories"] where taxonomy keys represent taxonomy-to-taxonomy relationships
    applies_to = Column(JSON, server_default="[]", nullable=False)

    def add_applies_to(self, value: str) -> None:
        """Add a target type or taxonomy key to applies_to."""
        current = set(self.applies_to or [])
        current.add(value)
        self.applies_to = list(current)

    def remove_applies_to(self, value: str) -> None:
        """Remove a target type or taxonomy key from applies_to."""
        current = set(self.applies_to or [])
        current.discard(value)
        self.applies_to = list(current)

    def can_apply_to_type(self, target_type: str) -> bool:
        """Check if this taxonomy can be applied to a given target type."""
        return target_type in (self.applies_to or [])

    def can_apply_to_taxonomy(self, taxonomy_key: str) -> bool:
        """Check if this taxonomy can be applied to another taxonomy."""
        # Check if the taxonomy key is in applies_to AND it's not a generic type
        return (
            taxonomy_key in (self.applies_to or [])
            and taxonomy_key not in TargetType.generic_types()
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
    Tracks actual applications of taxonomy elements to any target type.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "taxonomy_usage"

    # Source (the taxonomy element being applied)
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

    taxonomy_type = Column(String, nullable=False, index=True)

    # Target (what the taxonomy is being applied to)
    target_type = Column(String, nullable=False)  # "system", "dataset", "field", etc.
    target_identifier = Column(String, nullable=False)  # The ID/key of the target

    __table_args__ = (
        # Unique constraint to prevent duplicate applications
        UniqueConstraint(
            "source_element_key",
            "target_type",
            "target_identifier",
            name="uq_taxonomy_usage_application",
        ),
        # Composite index for common queries
        Index("ix_taxonomy_usage_lookup", "target_type", "target_identifier"),
        # Index for finding all usages by taxonomy type
        Index("ix_taxonomy_usage_by_taxonomy", "taxonomy_type", "target_type"),
    )
