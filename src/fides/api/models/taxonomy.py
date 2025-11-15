# pylint: disable=protected-access
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import (
    BOOLEAN,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import RelationshipProperty, Session, relationship

from fides.api.common_exceptions import KeyOrNameAlreadyExists, ValidationError
from fides.api.db.base_class import Base
from fides.api.models.sql_models import FidesBase  # type: ignore[attr-defined]

# Legacy Fideslang taxonomy keys
LEGACY_TAXONOMY_KEYS = {
    "data_category",
    "data_use",
    "data_subject",
}

# Taxonomies that are managed by Fides (legacy taxonomies and system group)
MANAGED_TAXONOMY_KEYS = {"data_category", "data_use", "data_subject", "system_group"}


class TargetType(str, Enum):
    """Enumeration of target types that taxonomies can apply to."""

    SYSTEM = "system"
    PRIVACY_DECLARATION = "privacy_declaration"
    TAXONOMY = "taxonomy"  # For taxonomy-to-taxonomy relationships


class Taxonomy(Base, FidesBase):
    """The SQL model for taxonomy resources.

    This is a generic taxonomy model that can be used to create any taxonomy.
    For now we seed the database with the legacy taxonomies (data_category, data use, data subject)
    so that these legacy taxonomy types can be used for allowed usage relationships.
    """

    # Overriding the id definition from Base so we don't treat this as the primary key
    id = Column(
        String(255),
        nullable=False,
        index=False,
        unique=True,
        default=FidesBase.generate_uuid,
    )

    # The fides_key is inherited from FidesBase and acts as the primary key

    # This is private to encourage the use of applies_to (see comment below)
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
    applies_to: List[str] = association_proxy(
        "_allowed_usages",
        "target_type",
        # Allow setting via strings, the relationship backref will set FK
        creator=lambda target_type: TaxonomyAllowedUsage(target_type=target_type),
    )

    @classmethod
    def create(
        cls: Type["Taxonomy"],
        db: Session,
        *,
        data: Dict[str, Any],
        check_name: bool = True,
    ) -> "Taxonomy":
        """Create a new Taxonomy with proper handling of applies_to."""
        # Disallow creating taxonomies that represent legacy types
        fides_key = data.get("fides_key")
        # Specifically exclude system_group to allow for creation during tests
        # We already have unique constraints on fides_key to prevent duplicates on DB level
        if fides_key in MANAGED_TAXONOMY_KEYS:
            raise ValidationError(
                f"Cannot create taxonomy '{fides_key}'. This is a taxonomy managed by the system."
            )
        applies_to = data.get("applies_to", [])

        # Create a copy of data without applies_to to avoid modifying the input
        data_without_applies_to = {
            key: value for key, value in data.items() if key != "applies_to"
        }

        # Create the taxonomy
        taxonomy: Taxonomy = super().create(
            db=db, data=data_without_applies_to, check_name=check_name
        )

        # Reconcile allowed usages if applies_to was provided
        if applies_to:
            taxonomy._reconcile_allowed_usages(db, applies_to)

        return cls.persist_obj(db, taxonomy)

    def update(self, db: Session, *, data: Dict[str, Any]) -> "Taxonomy":
        """Update a Taxonomy with proper handling of applies_to."""
        applies_to = data.get("applies_to", None)

        # Create a copy of data without applies_to to avoid modifying the input
        data_without_applies_to = {
            key: value for key, value in data.items() if key != "applies_to"
        }

        # Update the base fields
        super().update(db=db, data=data_without_applies_to)

        # If applies_to was provided, reconcile allowed usages
        if applies_to is not None:
            self._reconcile_allowed_usages(db, applies_to)

        return self

    def save(self, db: Session) -> "Taxonomy":
        """Override save to reconcile any direct `applies_to` edits before persisting.

        This allows callers to mutate `applies_to` via the association proxy and then call save.
        """
        # Ensure no duplicate target types and reconcile relationship objects to the current values
        self._reconcile_allowed_usages(db, list(self.applies_to))
        return super().save(db)  # type: ignore[return-value]

    def _reconcile_allowed_usages(self, db: Session, applies_to: List[str]) -> None:
        """Ensure `_allowed_usages` matches the provided `applies_to` list.

        - Deletes usages not in the provided list
        - Creates usages missing from the relationship
        - Deduplicates by target_type
        """
        existing_usages = {usage.target_type: usage for usage in self._allowed_usages}
        desired_types = set(applies_to)

        # Delete usages that should no longer exist
        for target_type in set(existing_usages.keys()) - desired_types:
            # Remove from relationship; delete-orphan cascade will handle DB delete
            self._allowed_usages.remove(existing_usages[target_type])

        # Add missing usages
        for target_type in desired_types - set(existing_usages.keys()):
            self._allowed_usages.append(TaxonomyAllowedUsage(target_type=target_type))

        # Deduplicate any accidental duplicates in-memory
        seen: set[str] = set()
        for usage in list(self._allowed_usages):
            if usage.target_type in seen:
                # Remove duplicate from relationship; delete-orphan will handle DB
                self._allowed_usages.remove(usage)
            else:
                seen.add(usage.target_type)


class TaxonomyAllowedUsage(Base):
    """
    The SQL model for taxonomy allowed usage.
    Defines what types of targets a taxonomy can be applied to.

    target_type can be either:
    - A generic type: "system", "privacy_declaration", "taxonomy"
    - A taxonomy key: "data_category", "data_use", etc.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "taxonomy_allowed_usage"

    id = Column(
        String(255),
        nullable=False,
        index=False,
        unique=True,
        default=FidesBase.generate_uuid,
    )

    source_taxonomy: RelationshipProperty[Taxonomy] = relationship(
        "Taxonomy",
        back_populates="_allowed_usages",
    )

    source_taxonomy_key: Column[str] = Column(
        String,
        ForeignKey("taxonomy.fides_key", ondelete="CASCADE"),
        primary_key=True,
    )
    target_type: Column[str] = Column(
        String, primary_key=True
    )  # Can be "system", "dataset", OR a taxonomy key like "data_category"


class TaxonomyElement(Base, FidesBase):
    """
    The SQL model for taxonomy elements.

    This is a generic taxonomy element model that can be used to create any taxonomy element.

    As of now the legacy taxonomy elements still exist in their own tables (ctl_data_categories, ctl_data_uses, ctl_data_subjects),
    but we can migrate them to this model in the future if needed.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "taxonomy_element"

    id = Column(
        String(255),
        nullable=False,
        index=False,
        unique=True,
        default=FidesBase.generate_uuid,
    )

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

    @classmethod
    def create(
        cls: Type["TaxonomyElement"],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = True,
    ) -> "TaxonomyElement":
        """
        Override create to skip name uniqueness check for hierarchical taxonomy.

        TaxonomyElement is hierarchical - fides_key provides sufficient uniqueness.
        Multiple elements can share the same name as long as their keys differ.
        """
        # Check if taxonomy element with same fides_key already exists within the same taxonomy_type
        if "fides_key" in data and data["fides_key"] and "taxonomy_type" in data:
            existing_by_key = (
                db.query(cls)
                .filter(
                    cls.fides_key == data["fides_key"],
                    cls.taxonomy_type == data["taxonomy_type"],
                )
                .first()
            )
            if existing_by_key:
                raise KeyOrNameAlreadyExists(
                    f'Taxonomy element with fides_key "{data["fides_key"]}" already exists in taxonomy "{data["taxonomy_type"]}".'
                )
        # Always skip name check - fides_key uniqueness is sufficient
        return super().create(db=db, data=data, check_name=False)

    def update(self, db: Session, *, data: dict[str, Any]) -> "TaxonomyElement":
        """
        Override update to check for existing taxonomy elements with the same fides_key
        within the same taxonomy_type when fides_key is being changed.
        """
        # Check if fides_key is being changed and if it conflicts with an existing element
        if (
            "fides_key" in data
            and data["fides_key"]
            and data["fides_key"] != self.fides_key
        ):
            # Ensure taxonomy_type is available (either in data or from self)
            taxonomy_type = data.get("taxonomy_type") or self.taxonomy_type
            if taxonomy_type:
                existing_by_key = (
                    db.query(TaxonomyElement)
                    .filter(
                        TaxonomyElement.fides_key == data["fides_key"],
                        TaxonomyElement.taxonomy_type == taxonomy_type,
                        TaxonomyElement.id != self.id,  # Exclude current element
                    )
                    .first()
                )
                if existing_by_key:
                    raise KeyOrNameAlreadyExists(
                        f'Taxonomy element with fides_key "{data["fides_key"]}" already exists in taxonomy "{taxonomy_type}".'
                    )
        return super().update(db=db, data=data)  # type: ignore[return-value]


class TaxonomyUsage(Base):
    """
    The SQL model for taxonomy usage.
    Tracks the application of taxonomy elements to other taxonomy elements.

    Example: Applying a "high" tag (from sensitivity taxonomy) to "user.contact.email" (from data_categories taxonomy).
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "taxonomy_usage"

    # The taxonomy element being applied (e.g., risk)
    source_element_key = Column(String, nullable=False, index=True)

    # The taxonomy element it's being applied to (e.g., a data category)
    target_element_key = Column(String, nullable=False, index=True)

    # Denormalized taxonomy types for validation and performance
    source_taxonomy = Column(String, nullable=False, index=True)
    target_taxonomy = Column(String, nullable=False, index=True)

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
    )
