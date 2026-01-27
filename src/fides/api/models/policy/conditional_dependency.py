from typing import TYPE_CHECKING, Any, Optional, Union

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import FidesBase
from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyBase,
    ConditionTypeAdapter,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
)

if TYPE_CHECKING:
    from fides.api.models.policy import Policy


class PolicyCondition(ConditionalDependencyBase):
    """Policy conditional dependencies - stores condition tree as JSONB.

    Used to define conditional logic for policy execution. Each policy can have
    a single condition tree that determines when the policy's rules should be applied.
    The entire condition tree is stored as a single JSONB object.

    Example Tree Structure (stored in condition_tree JSONB):
        {
            "logical_operator": "and",
            "conditions": [
                {"field_address": "request.country", "operator": "eq", "value": "EU"},
                {"field_address": "user.verified", "operator": "eq", "value": true}
            ]
        }
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "policy_condition"

    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)

    # Foreign key to policy
    policy_id = Column(
        String,
        ForeignKey("policy.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationship to policy
    policy = relationship("Policy", back_populates="conditions")

    # Ensure only one condition tree per policy
    __table_args__ = (
        UniqueConstraint(
            "policy_id",
            name="uq_policy_condition_policy_id",
        ),
    )

    @classmethod
    def get_condition_tree(
        cls,
        db: Session,
        **kwargs: Any,
    ) -> Optional[Union[ConditionLeaf, ConditionGroup]]:
        """Get the condition tree for a policy.

        Args:
            db: SQLAlchemy database session for querying
            **kwargs: Keyword arguments containing:
                policy_id: ID of the policy

        Returns:
            Optional[Union[ConditionLeaf, ConditionGroup]]: Root condition tree
                or None if no conditions exist

        Raises:
            ValueError: If policy_id is not provided

        Example:
            >>> # Get conditions for a policy
            >>> conditions = PolicyCondition.get_condition_tree(
            ...     db, policy_id=policy.id
            ... )
        """
        policy_id = kwargs.get("policy_id")

        if not policy_id:
            raise ValueError("policy_id is required as a keyword argument")

        condition_row = db.query(cls).filter(cls.policy_id == policy_id).one_or_none()

        if not condition_row or condition_row.condition_tree is None:
            return None

        return ConditionTypeAdapter.validate_python(condition_row.condition_tree)
