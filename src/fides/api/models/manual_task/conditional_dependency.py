from typing import TYPE_CHECKING, Any, Optional, Union

from sqlalchemy import Column, ForeignKey, Index, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import FidesBase
from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyBase,
    ConditionalDependencyType,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
)

if TYPE_CHECKING:
    from fides.api.models.manual_task.manual_task import ManualTask


class ManualTaskConditionalDependency(ConditionalDependencyBase):
    """Manual task conditional dependencies - single type hierarchy."""

    @declared_attr
    def __tablename__(cls) -> str:
        return "manual_task_conditional_dependency"

    # We need to redefine it here so that self-referential relationships
    # can properly reference the `id` column instead of the built-in Python function.
    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)
    # Foreign key relationships
    manual_task_id = Column(
        String, ForeignKey("manual_task.id", ondelete="CASCADE"), nullable=False
    )
    parent_id = Column(
        String,
        ForeignKey("manual_task_conditional_dependency.id", ondelete="CASCADE"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_manual_task_conditional_dependency_manual_task_id", "manual_task_id"),
        Index("ix_manual_task_conditional_dependency_parent_id", "parent_id"),
        Index("ix_manual_task_conditional_dependency_condition_type", "condition_type"),
        Index("ix_manual_task_conditional_dependency_sort_order", "sort_order"),
    )

    # Relationships
    task = relationship("ManualTask", back_populates="conditional_dependencies")
    parent = relationship(
        "ManualTaskConditionalDependency",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id],
    )
    children = relationship(
        "ManualTaskConditionalDependency",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_id],
    )

    @classmethod
    def get_root_condition(
        cls, db: Session, *args: Any, **kwargs: Any
    ) -> Optional[Union[ConditionLeaf, ConditionGroup]]:
        """Get the root condition for a manual task

        Args:
            db: Database session
            manual_task_id: ID of the manual task (first positional arg)
        """
        if not args:
            raise ValueError("manual_task_id is required as first positional argument")

        manual_task_id = args[0]
        root = (
            db.query(cls)
            .filter(cls.manual_task_id == manual_task_id, cls.parent_id.is_(None))
            .first()
        )

        if not root:
            return None

        if root.condition_type == ConditionalDependencyType.leaf:
            return root.to_condition_leaf()
        return root.to_condition_group()
