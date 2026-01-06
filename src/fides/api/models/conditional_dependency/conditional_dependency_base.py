from typing import Any, Optional

from pydantic import TypeAdapter
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base
from fides.api.task.conditional_dependencies.schemas import Condition

# TypeAdapter for deserializing JSONB to Condition (handles Union discrimination)
ConditionTypeAdapter: TypeAdapter[Condition] = TypeAdapter(Condition)


class ConditionalDependencyError(Exception):
    """Exception for conditional dependency errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ConditionalDependencyBase(Base):
    """Abstract base class for all conditional dependency models.

    This class provides a common structure for storing condition trees as a single JSONB object
    that can be evaluated to determine when certain actions should be taken.

    Architecture:
        - JSONB Storage: Full condition tree stored as a single JSONB object
        - Pydantic Integration: Uses Condition schema for serialization/deserialization
        - Single Row Per Entity: Each parent entity has one row containing its full condition tree

    Concrete Implementations:
        - ManualTaskConditionalDependency: Single condition tree per manual task
        - DigestCondition: Multi-type hierarchy with digest_condition_type separation
          - One row per (digest_config_id, digest_condition_type) combination

    Usage Pattern:
        1. Inherit from this base class
        2. Define your table name with @declared_attr
        3. Add foreign key relationships (parent_id, entity_id)
        4. Implement get_condition_tree() classmethod
        5. Add any domain-specific columns

    Example Tree Structure (stored in condition_tree JSONB):
        {
            "logical_operator": "and",
            "conditions": [
                {"field_address": "user.role", "operator": "eq", "value": "admin"},
                {"field_address": "request.priority", "operator": "gte", "value": 3},
                {
                    "logical_operator": "or",
                    "conditions": [
                        {"field_address": "user.department", "operator": "eq", "value": "security"},
                        {"field_address": "user.department", "operator": "eq", "value": "compliance"}
                    ]
                }
            ]
        }

    Note:
        - This is a SQLAlchemy abstract model (__abstract__ = True)
        - No database table is created for this base class
        - Subclasses must implement get_condition_tree()
    """

    __abstract__ = True

    # JSONB storage for full condition tree
    condition_tree = Column(JSONB, nullable=True)

    @classmethod
    def get_condition_tree(cls, db: Session, **kwargs: Any) -> Optional[Condition]:
        """Get the condition tree for a parent entity.

        This abstract method must be implemented by concrete subclasses to define
        how to retrieve the condition tree for their specific use case.

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
            f"Subclasses of {cls.__name__} must implement get_condition_tree(). "
            f"This method should query for the condition tree and return it as a Condition schema object, or None if not found. "
            f"See the docstring for implementation guidelines and examples."
        )
