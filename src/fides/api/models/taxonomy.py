from __future__ import annotations

from enum import Enum
from typing import List, Optional, Set

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
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import RelationshipProperty, relationship

from fides.api.db.base_class import Base
from fides.api.models.sql_models import FidesBase  # type: ignore[attr-defined]


class TargetType(str, Enum):
    """Enumeration of target types that taxonomies can apply to."""

    TAXONOMY = "taxonomy"
    SYSTEM = "system"
    DATASET = "dataset"
    COLLECTION = "collection"
    FIELD = "field"
    PRIVACY_DECLARATION = "privacy_declaration"


class Taxonomy(Base, FidesBase):
    """
    The SQL model for taxonomy resources.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "taxonomy"

    fides_key = Column(String, primary_key=True, index=True, unique=True)

    _allowed_usages: RelationshipProperty[List[TaxonomyAllowedUsage]] = relationship(
        "TaxonomyAllowedUsage",
        foreign_keys="TaxonomyAllowedUsage.source_taxonomy_key",
        cascade="all, delete-orphan",
    )

    @property
    def applies_to(self) -> Set[str]:
        """
        Get simple string representation for easy manipulation.
        Returns target_types for generic relationships, taxonomy_keys for specific ones.
        Uses a set to automatically handle duplicates.

        Examples:
        - {"system", "dataset", "data_categories"} - can apply to any system/dataset + data_categories taxonomy
        """
        result: Set[str] = set()
        for usage in self._allowed_usages:
            if (
                usage.target_type == TargetType.TAXONOMY.value
                and usage.target_taxonomy_key
            ):
                result.add(usage.target_taxonomy_key)
            else:
                result.add(usage.target_type)
        return result

    @applies_to.setter
    def applies_to(self, values: Set[str]) -> None:
        """
        Set target relationships using simple string values.
        Automatically determines if string is a target_type or taxonomy_key.
        Accepts either a set or list for convenience.

        Examples:
        - "system" -> {"target_type": "system"}
        - "data_categories" -> {"target_type": "taxonomy", "target_taxonomy_key": "data_categories"}
        """
        from sqlalchemy.orm import object_session

        session = object_session(self)
        if not session:
            raise RuntimeError(
                "Taxonomy must be attached to a session to modify applies_to"
            )

        # Clear existing relationships
        for usage in list(
            self._allowed_usages
        ):  # Create copy to avoid modification during iteration
            session.delete(usage)

        # Add new relationships
        for value in values:
            if self._is_target_type(value):
                # Generic target type
                usage = TaxonomyAllowedUsage(  # type: ignore[misc]
                    source_taxonomy_key=self.fides_key, target_type=value
                )
            else:
                # Assume it's a taxonomy key
                usage = TaxonomyAllowedUsage(  # type: ignore[misc]
                    source_taxonomy_key=self.fides_key,
                    target_type=TargetType.TAXONOMY.value,
                    target_taxonomy_key=value,
                )
            session.add(usage)

    def _is_target_type(self, value: str) -> bool:
        """Check if a string represents a generic target type vs taxonomy key."""
        try:
            # Use TargetType enum values (excluding TAXONOMY which is for taxonomy-to-taxonomy relationships)
            return value in {
                target_type.value
                for target_type in TargetType
                if target_type != TargetType.TAXONOMY
            }
        except AttributeError:
            return False


class TaxonomyAllowedUsage(Base):
    """
    The SQL model for taxonomy allowed usage.
    Defines what types of targets a taxonomy can be applied to.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "taxonomy_allowed_usage"

    source_taxonomy_key = Column(
        String,
        ForeignKey("taxonomy.fides_key", ondelete="CASCADE"),
        primary_key=True,
        index=True,  # Add index for foreign key
    )
    target_type = Column(
        String, primary_key=True
    )  # e.g., "system", "dataset", "taxonomy"
    target_taxonomy_key = Column(
        String, nullable=True, index=True  # Add index for taxonomy-to-taxonomy lookups
    )

    __table_args__ = (
        # Composite index for common queries
        Index("ix_allowed_usage_lookup", "source_taxonomy_key", "target_type"),
        # Ensure unique combinations
        UniqueConstraint(
            "source_taxonomy_key",
            "target_type",
            "target_taxonomy_key",
            name="uq_allowed_usage_combination",
        ),
    )


class TaxonomyElement(Base, FidesBase):
    """
    The SQL model for taxonomy elements.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "taxonomy_element"

    # Override the id field from FidesBase to not be a primary key
    id = Column(String(255), index=True, default=FidesBase.generate_uuid)

    # Use fides_key as the actual primary key
    fides_key = Column(String, primary_key=True, index=True, unique=True)

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
        remote_side=[fides_key],
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
        ForeignKey("taxonomy_element.fides_key", ondelete="CASCADE"),
        primary_key=True,
        index=True,  # Add index for foreign key
    )

    # Target (what the taxonomy is being applied to)
    target_type = Column(String, primary_key=True)  # "system", "dataset", "field", etc.
    target_identifier = Column(String, primary_key=True)  # The ID/key of the target

    __table_args__ = (
        # Composite index for common queries
        Index("ix_taxonomy_usage_lookup", "target_type", "target_identifier"),
        # Index for finding all usages of elements from a specific taxonomy
        Index("ix_taxonomy_usage_by_source", "source_element_key", "target_type"),
        # Named constraint for better error messages
        ForeignKeyConstraint(
            ["source_element_key"],
            ["taxonomy_element.fides_key"],
            name="fk_taxonomy_usage_source_element",
            ondelete="CASCADE",
        ),
    )
