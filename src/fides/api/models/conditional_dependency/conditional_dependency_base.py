from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import TypeAdapter
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

if TYPE_CHECKING:
    from sqlalchemy.orm.relationships import RelationshipProperty


# TypeAdapter for deserializing JSONB to Condition (handles Union discrimination)
ConditionTypeAdapter: TypeAdapter[Condition] = TypeAdapter(Condition)


class ConditionalDependencyError(Exception):
    """Exception for conditional dependency errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ConditionalDependencyType(str, Enum):
    """Shared enum for conditional dependency node types.

    Attributes:
        leaf: Individual condition (field_address + operator + value)
        group: Collection of conditions with logical operator (AND/OR)
    """

    leaf = "leaf"
    group = "group"


class ConditionalDependencyBase(Base):
    """Abstract base class for all conditional dependency models.

    This class provides a common structure for building hierarchical condition trees
    or storing condition trees as a single JSONB object.
    that can be evaluated to determine when certain actions should be taken.

    Architecture:
        - JSONB Storage: Full condition tree stored as a single JSONB object
        - Pydantic Integration: Uses Condition schema for serialization/deserialization
        - Tree Structure: Supports parent-child relationships for complex logic
        - Two Node Types: 'leaf' (individual conditions) and 'group' (logical operators)
        - Flexible Schema: Uses JSONB for dynamic value storage
        - Ordered Evaluation: sort_order ensures predictable condition processing

    Concrete Implementations:
        - ManualTaskConditionalDependency: Single-type hierarchy for manual tasks
          - Single-type hierarchy means one condition tree per manual task, this condition
            may be a nested group of conditions or a single leaf condition.
        - DigestCondition: Multi-type hierarchy with digest_condition_type separation
          - Multi-type hierarchy means one digest_config can have multiple independent
            condition trees, each with a different digest_condition_type (RECEIVER, CONTENT, PRIORITY)
          - Within each tree, all nodes must have the same digest_condition_type
          - This enables separate condition logic for different aspects of digest processing

    Usage Pattern:
        1. Inherit from this base class
        2. Define your table name with @declared_attr
        3. Add foreign key relationships (parent_id, entity_id)
        4. Implement get_root_condition() classmethod
        5. Add any domain-specific columns

    Example Tree Structure:
        Root Group (AND)
        ├── Leaf: user.role == "admin"
        ├── Leaf: request.priority >= 3
        └── Child Group (OR)
            ├── Leaf: user.department == "security"
            └── Leaf: user.department == "compliance"

    Note:
        - This is a SQLAlchemy abstract model (__abstract__ = True)
        - No database table is created for this base class
        - Subclasses must implement get_root_condition()
        - The 'children' relationship must be defined in concrete subclasses
    """

    __abstract__ = True

    # JSONB storage for full condition tree
    # Contains the entire condition tree as a single JSONB object.
    # Format matches Condition schema: either ConditionLeaf or ConditionGroup structure.
    condition_tree = Column(JSONB, nullable=True)

    # Tree structure - parent_id defined in concrete classes for proper foreign keys
    condition_type = Column(
        EnumColumn(ConditionalDependencyType), nullable=False, index=True
    )

    # Condition details (for leaf nodes)
    field_address = Column(String(255), nullable=True)  # For leaf conditions
    operator = Column(String, nullable=True)  # For leaf conditions
    value = Column(JSONB, nullable=True)  # For leaf conditions
    logical_operator = Column(String, nullable=True)  # 'and' or 'or' for groups

    # Ordering
    sort_order = Column(Integer, nullable=False, default=0, index=True)

    def to_correct_condition_type(self) -> Union[ConditionLeaf, ConditionGroup]:
        """Convert this database model to the correct condition type."""
        if self.condition_type == ConditionalDependencyType.leaf:
            return self.to_condition_leaf()
        return self.to_condition_group()

    def to_condition_leaf(self) -> ConditionLeaf:
        """Convert this database model to a ConditionLeaf schema object.

        This method transforms a leaf-type conditional dependency from its database
        representation into a structured ConditionLeaf object that can be used for
        evaluation and serialization.

        Returns:
            ConditionLeaf: Schema object containing field_address, operator, and value

        Raises:
            ValueError: If this condition is not a leaf type (i.e., it's a group)

        Example:
            >>> condition = SomeConcreteConditionalDependency(
            ...     condition_type="leaf",
            ...     field_address="user.role",
            ...     operator="eq",
            ...     value="admin"
            ... )
            >>> leaf = condition.to_condition_leaf()
            >>> print(leaf.field_address)  # "user.role"
        """
        if self.condition_type != ConditionalDependencyType.leaf:
            raise ValueError(
                f"Cannot convert {self.condition_type} condition to leaf. "
                f"Only conditions with condition_type='leaf' can be converted to ConditionLeaf. "
                f"This condition has type '{self.condition_type}' and should be converted using to_condition_group()."
            )

        return ConditionLeaf(
            field_address=self.field_address, operator=self.operator, value=self.value
        )

    def to_condition_group(self) -> ConditionGroup:
        """Convert this database model to a ConditionGroup schema object.

        This method transforms a group-type conditional dependency from its database
        representation into a structured ConditionGroup object. It recursively processes
        all child conditions, maintaining the tree structure and sort order.

        Returns:
            ConditionGroup: Schema object containing logical_operator and child conditions

        Raises:
            ValueError: If this condition is not a group type (i.e., it's a leaf)
            AttributeError: If the 'children' relationship is not properly defined

        Example:
            >>> # Assume we have a group with two leaf children
            >>> group_condition = SomeConcreteConditionalDependency(
            ...     condition_type="group",
            ...     logical_operator="and"
            ... )
            >>> condition_group = group_condition.to_condition_group()
            >>> print(condition_group.logical_operator)  # "and"
            >>> print(len(condition_group.conditions))   # 2
        """
        if self.condition_type != ConditionalDependencyType.group:
            raise ValueError(
                f"Cannot convert {self.condition_type} condition to group. "
                f"Only conditions with condition_type='group' can be converted to ConditionGroup. "
                f"This condition has type '{self.condition_type}' and should be converted using to_condition_leaf()."
            )

        # Recursively build children - note: 'children' must be defined in concrete classes
        try:
            children_list = [child for child in self.children]  # type: ignore[attr-defined]
        except AttributeError:
            raise AttributeError(
                f"The 'children' relationship is not defined on {self.__class__.__name__}. "
                f"Concrete subclasses must define a 'children' relationship for group conditions to work properly."
            )

        child_conditions = []
        for child in sorted(children_list, key=lambda x: x.sort_order):
            if child.condition_type == ConditionalDependencyType.leaf:
                child_conditions.append(child.to_condition_leaf())
            elif child.condition_type == ConditionalDependencyType.group:
                child_conditions.append(child.to_condition_group())
            else:
                raise ValueError(
                    f"Unknown condition_type '{child.condition_type}' found in child condition. "
                    f"Expected '{ConditionalDependencyType.leaf}' or '{ConditionalDependencyType.group}'."
                )

        return ConditionGroup(
            logical_operator=self.logical_operator, conditions=child_conditions
        )

    @classmethod
    def get_root_condition(cls, db: Session, **kwargs: Any) -> Optional[Condition]:
        """Get the condition tree for a parent entity.

        This abstract method must be implemented by concrete subclasses to define
        how to retrieve the condition tree for their specific use case.
        The root condition represents the top-level node in a condition tree.

        Args:
            db: SQLAlchemy database session for querying
            **kwargs: Keyword arguments specific to each implementation.
                    Examples:
                    - manual_task_id: ID of the manual task
                    - digest_config_id: ID of the digest config
                    - digest_condition_type: Type of digest condition (RECEIVER, CONTENT, PRIORITY)

        Returns:
            Optional[Condition]: Root condition tree (ConditionLeaf or ConditionGroup) or None
                               if no conditions exist for the specified criteria

        Raises:
            NotImplementedError: If called on the base class directly

        """
        raise NotImplementedError(
            f"Subclasses of {cls.__name__} must implement get_root_condition(). "
            f"This method should query for the root condition (parent_id=None) "
            f"and return it as a Condition schema object, or None if not found. "
            f"See the docstring for implementation guidelines and examples."
        )
