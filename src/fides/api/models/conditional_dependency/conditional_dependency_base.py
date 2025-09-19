from enum import Enum
from typing import Any, Optional

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base
from fides.api.db.util import EnumColumn
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
)


class ConditionalDependencyType(str, Enum):
    """Shared enum for conditional dependency node types."""

    leaf = "leaf"
    group = "group"


class ConditionalDependencyBase(Base):
    """Abstract base class for all conditional dependency models."""

    __abstract__ = True

    # Tree structure - parent_id defined in concrete classes for proper foreign keys
    condition_type = Column(EnumColumn(ConditionalDependencyType), nullable=False)

    # Condition details (for leaf nodes)
    field_address = Column(String(255), nullable=True)  # For leaf conditions
    operator = Column(String, nullable=True)  # For leaf conditions
    value = Column(JSONB, nullable=True)  # For leaf conditions
    logical_operator = Column(String, nullable=True)  # 'and' or 'or' for groups

    # Ordering
    sort_order = Column(Integer, nullable=False, default=0)

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
        cls, db: Session, *args: Any, **kwargs: Any
    ) -> Optional[Condition]:
        """Get the root condition for a parent entity - implemented by subclasses

        Args:
            db: Database session
            *args: Additional positional arguments specific to each implementation
            **kwargs: Additional keyword arguments specific to each implementation

        Returns:
            Optional[Condition]: Root condition or None if not found
        """
        raise NotImplementedError("Subclasses must implement get_root_condition")
