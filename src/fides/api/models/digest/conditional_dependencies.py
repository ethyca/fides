from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Union

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import FidesBase
from fides.api.db.util import EnumColumn
from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyBase,
    ConditionalDependencyError,
    ConditionTypeAdapter,
)
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
)

if TYPE_CHECKING:
    from fides.api.models.digest.digest_config import DigestConfig

from enum import StrEnum


class DigestConditionType(StrEnum):
    """Types of digest conditions - each can have their own tree.

    Types:
        - RECEIVER: Conditions that determine who gets the digest
        - CONTENT: Conditions that determine what gets included in the digest
        - PRIORITY: Conditions that determine what is considered high priority for the digest
          - This could be used to determine sending the digest at a different time or how
            often it should be sent. It could also be used to format content.
          - Example:
            - DSRs that are due within the next week
            - Privacy requests that are due within the next week
            - Privacy requests for certain geographic regions
    """

    RECEIVER = "receiver"
    CONTENT = "content"
    PRIORITY = "priority"


class DigestCondition(ConditionalDependencyBase):
    """Digest conditional dependencies - stores condition tree as JSONB.

    Each digest_config can have up to three independent condition trees,
    one per digest_condition_type (RECEIVER, CONTENT, PRIORITY).
    Within each tree, all nodes must have the same digest_condition_type
    This enables separate condition logic for different aspects of digest processing.

    Example Tree Structure:
        DigestConfig (e.g., "Weekly Privacy Digest")
        ├── RECEIVER condition_tree (who gets the digest)
        │   └── {"logical_operator": "and", "conditions": [...]}
        ├── CONTENT condition_tree (what gets included)
        │   └── {"logical_operator": "or", "conditions": [...]}
        └── PRIORITY condition_tree (what is high priority)
            └── {"field_address": "task.count", "operator": "gte", "value": 5}
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "digest_condition"

    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)

    # Foreign key to parent digest config
    digest_config_id = Column(
        String(255),
        ForeignKey("digest_config.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Condition category - determines which aspect of digest this condition controls
    digest_condition_type = Column(
        EnumColumn(DigestConditionType), nullable=False, index=True
    )

    # Relationship to parent config
    digest_config = relationship("DigestConfig", back_populates="conditions")

    # Ensure only one condition per (digest_config_id, digest_condition_type) combination
    __table_args__ = (
        UniqueConstraint(
            "digest_config_id",
            "digest_condition_type",
            name="uq_digest_condition_config_type",
        ),
    )

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = True,
    ) -> "DigestCondition":
        """Create a new DigestCondition."""
        try:
            return super().create(db=db, data=data, check_name=check_name)
        except Exception as e:
            raise ConditionalDependencyError(str(e))

    @classmethod
    def get_condition_tree(
        cls,
        db: Session,
        **kwargs: Any,
    ) -> Optional[Union[ConditionLeaf, ConditionGroup]]:
        """Get the condition tree for a specific digest condition type.

        Each digest_config can have separate condition trees for RECEIVER, CONTENT, and PRIORITY
        types. This method retrieves the condition tree for a specific type.

        Args:
            db: SQLAlchemy database session for querying
            **kwargs: Keyword arguments containing:
                digest_config_id: ID of the digest config
                digest_condition_type: DigestConditionType enum value
                                     Must be one of: RECEIVER, CONTENT, PRIORITY

        Returns:
            Optional[Union[ConditionLeaf, ConditionGroup]]: Condition tree for the specified type

        Raises:
            ValueError: If required parameters are missing

        Example:
            >>> # Get receiver conditions for a digest
            >>> receiver_conditions = DigestCondition.get_condition_tree(
            ...     db, digest_config_id=digest_config.id,
            ...     digest_condition_type=DigestConditionType.RECEIVER
            ... )
            >>> # Get content conditions for the same digest
            >>> content_conditions = DigestCondition.get_condition_tree(
            ...     db, digest_config_id=digest_config.id,
            ...     digest_condition_type=DigestConditionType.CONTENT
            ... )
        """
        digest_config_id = kwargs.get("digest_config_id")
        digest_condition_type = kwargs.get("digest_condition_type")

        if not digest_config_id or not digest_condition_type:
            raise ValueError(
                "digest_config_id and digest_condition_type are required keyword arguments"
            )

        condition_row = (
            db.query(cls)
            .filter(
                cls.digest_config_id == digest_config_id,
                cls.digest_condition_type == digest_condition_type,
            )
            .one_or_none()
        )

        if not condition_row or condition_row.condition_tree is None:
            return None

        return ConditionTypeAdapter.validate_python(condition_row.condition_tree)

    @classmethod
    def get_all_condition_trees(
        cls, db: Session, digest_config_id: str
    ) -> dict[DigestConditionType, Optional[Condition]]:
        """Get condition trees for all digest condition types"""
        return {
            condition_type: cls.get_condition_tree(
                db,
                digest_config_id=digest_config_id,
                digest_condition_type=condition_type,
            )
            for condition_type in DigestConditionType
        }
