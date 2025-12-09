from typing import TYPE_CHECKING, Any, Optional, Union

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import FidesBase
from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyBase,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
)

if TYPE_CHECKING:
    from fides.api.models.policy import Policy


class PolicyCondition(ConditionalDependencyBase):
    """Policy conditional dependencies - single type hierarchy.

    Used to define conditional logic for policy execution. Each policy can have
    a single condition tree (root condition with optional nested children) that
    determines when the policy's rules should be applied.

    Example Tree Structure:
        Policy (e.g., "GDPR Access Request")
        └── Condition Tree
            └── Group (AND)
                ├── Leaf: request.country == "EU"
                └── Leaf: user.verified == true
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "policy_condition"

    # We need to redefine it here so that self-referential relationships
    # can properly reference the `id` column instead of the built-in Python function.
    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)

    # Foreign key relationships
    policy_id = Column(
        String,
        ForeignKey("policy.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id = Column(
        String,
        ForeignKey("policy_condition.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Relationships
    policy = relationship("Policy", back_populates="conditions")
    parent = relationship(
        "PolicyCondition",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id],
    )
    children = relationship(
        "PolicyCondition",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_id],
    )

    @classmethod
    def get_root_condition(
        cls, db: Session, **kwargs: Any
    ) -> Optional[Union[ConditionLeaf, ConditionGroup]]:
        """Get the root condition for a policy.

        Args:
            db: Database session
            **kwargs: Keyword arguments containing:
                policy_id: ID of the policy

        Returns:
            Optional[Union[ConditionLeaf, ConditionGroup]]: Root condition tree
                or None if no conditions exist

        Raises:
            ValueError: If policy_id is not provided
        """
        policy_id = kwargs.get("policy_id")

        if not policy_id:
            raise ValueError("policy_id is required as a keyword argument")

        root = (
            db.query(cls)
            .filter(cls.policy_id == policy_id, cls.parent_id.is_(None))
            .first()
        )

        if not root:
            return None

        return root.to_correct_condition_type()
