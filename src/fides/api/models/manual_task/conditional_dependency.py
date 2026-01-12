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
    from fides.api.models.manual_task.manual_task import ManualTask


class ManualTaskConditionalDependency(ConditionalDependencyBase):
    """Manual task conditional dependency - stores condition tree as JSONB.

    Each manual task can have one condition tree that determines when the task
    should be created or executed based on privacy request data.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "manual_task_conditional_dependency"

    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)

    # Foreign key to parent manual task - one condition tree per task
    manual_task_id = Column(
        String,
        ForeignKey("manual_task.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Relationship to parent manual task
    task = relationship("ManualTask", back_populates="conditional_dependencies")

    __table_args__ = (
        UniqueConstraint(
            "manual_task_id", name="uq_manual_task_conditional_dependency"
        ),
    )

    @classmethod
    def get_condition_tree(
        cls, db: Session, **kwargs: Any
    ) -> Optional[Union[ConditionLeaf, ConditionGroup]]:
        """Get the condition tree for a manual task

        Args:
            db: Database session
            **kwargs: Keyword arguments containing:
                manual_task_id: ID of the manual task

        Returns:
            Optional[Union[ConditionLeaf, ConditionGroup]]: The condition tree,
                or None if no conditions exist for this task

        Raises:
            ValueError: If manual_task_id is not provided
        """
        manual_task_id = kwargs.get("manual_task_id")

        if not manual_task_id:
            raise ValueError("manual_task_id is required as a keyword argument")

        condition_row = (
            db.query(cls).filter(cls.manual_task_id == manual_task_id).one()
        )

        if not condition_row or condition_row.condition_tree is None:
            return None

        return ConditionTypeAdapter.validate_python(condition_row.condition_tree)
