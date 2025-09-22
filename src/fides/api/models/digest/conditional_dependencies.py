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
    """Digest conditional dependencies - multi-type hierarchies."""

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
