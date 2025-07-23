from enum import Enum
from typing import TYPE_CHECKING, Optional, Union

from sqlalchemy import Column, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base, FidesBase
from fides.api.db.util import EnumColumn
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
)

if TYPE_CHECKING:
    from fides.api.models.manual_task.manual_task import ManualTask


class ManualTaskConditionalDependencyType(str, Enum):
    """Enum for manual task conditional dependency types.

    This enum defines the two types of nodes in a conditional dependency tree:

    - leaf: A terminal node that represents a single condition (e.g., "user.age >= 18")
    - group: A non-terminal node that groups multiple conditions with logical operators (AND/OR)

    Examples:
        leaf: Used for simple field comparisons like:
            - "user.name exists"
            - "user.age >= 18"
            - "billing.subscription.status == 'active'"

        group: Used to combine multiple conditions with logical operators:
            - AND group: "user.age >= 18 AND user.active == true"
            - OR group: "user.role == 'admin' OR user.verified == true"
            - Nested groups: "(user.age >= 18 AND (user.role == 'admin' OR user.verified == true))"
    """

    leaf = "leaf"
    group = "group"


class ManualTaskConditionalDependency(Base):
    """Model for storing conditional dependencies."""

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
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

    # Condition metadata
    condition_type = Column(
        EnumColumn(ManualTaskConditionalDependencyType), nullable=False
    )  # leaf or group
    field_address = Column(String, nullable=True)  # For leaf conditions
    operator = Column(String, nullable=True)  # For leaf conditions
    value = Column(JSONB, nullable=True)  # For leaf conditions
    logical_operator = Column(String, nullable=True)  # 'and' or 'or' for groups

    # Ordering
    sort_order = Column(Integer, nullable=False, default=0)

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

    def to_condition_leaf(self) -> ConditionLeaf:
        """Convert to ConditionLeaf if this is a leaf condition"""
        if self.condition_type != "leaf":
            raise ValueError("Cannot convert group condition to leaf")

        return ConditionLeaf(
            field_address=self.field_address, operator=self.operator, value=self.value
        )

    def to_condition_group(self) -> ConditionGroup:
        """Convert to ConditionGroup if this is a group condition"""
        if self.condition_type != "group":
            raise ValueError("Cannot convert leaf condition to group")

        # Recursively build children
        child_conditions = []
        children_list = [child for child in self.children]  # type: ignore[attr-defined]
        for child in sorted(children_list, key=lambda x: x.sort_order):
            if child.condition_type == "leaf":
                child_conditions.append(child.to_condition_leaf())
            else:
                child_conditions.append(child.to_condition_group())

        return ConditionGroup(
            logical_operator=self.logical_operator, conditions=child_conditions
        )

    @classmethod
    def get_root_condition(
        cls, db: Session, manual_task_id: str
    ) -> Optional[Union[ConditionLeaf, ConditionGroup]]:
        """Get the root condition for a config"""
        root = (
            db.query(cls)
            .filter(cls.manual_task_id == manual_task_id, cls.parent_id.is_(None))
            .first()
        )

        if not root:
            return None

        if root.condition_type == "leaf":
            return root.to_condition_leaf()

        return root.to_condition_group()
