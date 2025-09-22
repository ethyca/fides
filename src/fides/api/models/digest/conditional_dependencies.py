from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Union

from sqlalchemy import Column, ForeignKey, Index, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import FidesBase
from fides.api.db.util import EnumColumn
from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyBase,
    ConditionalDependencyType,
)
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
)

if TYPE_CHECKING:
    from fides.api.models.digest.digest_config import DigestConfig


class DigestConditionType(str, Enum):
    """Types of digest conditions - each can have their own tree."""

    RECEIVER = "receiver"
    CONTENT = "content"
    PRIORITY = "priority"


class DigestCondition(ConditionalDependencyBase):
    """Digest conditional dependencies - multi-type hierarchies.

    Ensures that all conditions within the same tree have the same digest_condition_type.
    This prevents logical errors where different condition types are mixed in a single
    condition tree structure.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "digest_condition"

    # We need to redefine it here so that self-referential relationships
    # can properly reference the `id` column instead of the built-in Python function.
    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)

    # Foreign key relationships
    digest_config_id = Column(
        String(255), ForeignKey("digest_config.id", ondelete="CASCADE"), nullable=False
    )
    parent_id = Column(
        String(255),
        ForeignKey("digest_condition.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Digest-specific: condition category
    digest_condition_type = Column(EnumColumn(DigestConditionType), nullable=False)

    # Relationships
    digest_config = relationship("DigestConfig", back_populates="conditions")
    parent = relationship(
        "DigestCondition",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id],
    )
    children = relationship(
        "DigestCondition",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_id],
    )

    __table_args__ = (
        Index("ix_digest_condition_digest_config_id", "digest_config_id"),
        Index("ix_digest_condition_parent_id", "parent_id"),
        Index("ix_digest_condition_digest_condition_type", "digest_condition_type"),
        Index("ix_digest_condition_condition_type", "condition_type"),
        Index("ix_digest_condition_sort_order", "sort_order"),
    )

    def _validate_condition_type_consistency(
        self, db: Session, data: dict[str, Any]
    ) -> None:
        """Validate that all conditions in the same tree have the same digest_condition_type."""
        parent_id = data.get("parent_id") or getattr(self, "parent_id", None)
        digest_condition_type = data.get("digest_condition_type") or getattr(
            self, "digest_condition_type", None
        )

        if not parent_id:
            # Root condition - no validation needed
            return

        # Get the parent condition
        parent = (
            db.query(DigestCondition).filter(DigestCondition.id == parent_id).first()
        )
        if not parent:
            raise ValueError(f"Parent condition with id '{parent_id}' does not exist")

        # Check if parent has the same digest_condition_type
        if parent.digest_condition_type != digest_condition_type:
            raise ValueError(
                f"Cannot create condition with type '{digest_condition_type}' under parent "
                f"with type '{parent.digest_condition_type}'. All conditions in the same tree "
                f"must have the same digest_condition_type."
            )

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = True,
    ) -> "DigestCondition":
        """Create a new DigestCondition with validation."""
        # Create a temporary instance for validation
        temp_instance = cls()
        temp_instance._validate_condition_type_consistency(db, data)

        # If validation passes, create normally
        return super().create(db=db, data=data, check_name=check_name)

    def update(self, db: Session, *, data: dict[str, Any]) -> "DigestCondition":
        """Update DigestCondition with validation."""
        # Validate before updating
        self._validate_condition_type_consistency(db, data)

        # If validation passes, update normally
        return super().update(db=db, data=data)  # type: ignore[return-value]

    @classmethod
    def get_root_condition(
        cls, db: Session, *args: Any, **kwargs: Any
    ) -> Optional[Union[ConditionLeaf, ConditionGroup]]:
        """Get the root condition for a specific digest condition type

        Args:
            db: Database session
            digest_config_id: ID of the digest config (first positional arg)
            condition_type: Type of digest condition (second positional arg)
        """
        if len(args) < 2:
            raise ValueError(
                "digest_config_id and condition_type are required as positional arguments"
            )

        digest_config_id, condition_type = args[0], args[1]
        root = (
            db.query(cls)
            .filter(
                cls.digest_config_id == digest_config_id,
                cls.digest_condition_type == condition_type,
                cls.parent_id.is_(None),
            )
            .first()
        )

        if not root:
            return None

        if root.condition_type == ConditionalDependencyType.leaf:
            return root.to_condition_leaf()
        return root.to_condition_group()

    @classmethod
    def get_all_root_conditions(
        cls, db: Session, digest_config_id: str
    ) -> dict[DigestConditionType, Optional[Condition]]:
        """Get root conditions for all digest condition types"""
        return {
            condition_type: cls.get_root_condition(db, digest_config_id, condition_type)
            for condition_type in DigestConditionType
        }
