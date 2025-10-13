from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Union

from sqlalchemy import Column, ForeignKey, Index, String, text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import FidesBase
from fides.api.db.util import EnumColumn
from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyBase,
    ConditionalDependencyError,
)
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
)

if TYPE_CHECKING:
    from fides.api.models.digest.digest_config import DigestConfig


class DigestConditionType(str, Enum):
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
    """Digest conditional dependencies - multi-type hierarchies.

    - Multi-type hierarchy means one digest_config can have multiple independent
      condition trees, each with a different digest_condition_type (RECEIVER, CONTENT, PRIORITY)
    - Within each tree, all nodes must have the same digest_condition_type
    - This enables separate condition logic for different aspects of digest processing

    Ensures that all conditions within the same tree have the same digest_condition_type.
    This prevents logical errors where different condition types are mixed in a single
    condition tree structure.

    Example Tree Structure:
        DigestConfig (e.g., "Weekly Privacy Digest")
        ├── RECEIVER Dependency Condition Tree (who gets the digest)
        │   └── Group (AND)
        │       ├── Leaf: user.role == "admin"
        │       └── Leaf: user.department == "privacy"
        ├── CONTENT Dependency Condition Tree (what gets included)
        │   └── Group (OR)
        │       ├── Leaf: task.priority == "high"
        │       └── Leaf: task.overdue == true
        └── PRIORITY Dependency Condition Tree (when to send)
            └── Leaf: task.count >= 5
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "digest_condition"

    # We need to redefine it here so that self-referential relationships
    # can properly reference the `id` column instead of the built-in Python function.
    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)

    # Foreign key relationships
    digest_config_id = Column(
        String(255),
        ForeignKey("digest_config.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id = Column(
        String(255),
        ForeignKey("digest_condition.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Digest-specific: condition category
    digest_condition_type = Column(
        EnumColumn(DigestConditionType), nullable=False, index=True
    )

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

    # Ensure only one root condition per digest_condition_type per digest_config
    __table_args__ = (
        Index(
            "ix_digest_condition_unique_root_per_type",
            "digest_config_id",
            "digest_condition_type",
            unique=True,
            postgresql_where=text("parent_id IS NULL"),
        ),
    )

    @staticmethod
    def _validate_condition_type_consistency(db: Session, data: dict[str, Any]) -> None:
        """Validate that a condition's digest_condition_type matches its parent's type.

        Since each parent was validated when created, checking against the immediate parent
        is sufficient to ensure tree-wide consistency.

        Args:
            db: Database session for querying
            data: Dictionary containing condition data to validate (must include both parent_id and digest_condition_type)

        Raises:
            ValueError: If parent doesn't exist or digest_condition_type doesn't match parent's type
        """
        parent_id = data.get("parent_id")
        digest_condition_type = data.get("digest_condition_type")

        if not parent_id:
            # Root condition - no validation needed
            return

        # Get the parent condition
        parent = (
            db.query(DigestCondition).filter(DigestCondition.id == parent_id).first()
        )
        if not parent:
            raise ValueError(f"Parent condition with id '{parent_id}' does not exist")

        # Validate that the new condition matches the parent's digest_condition_type
        if parent.digest_condition_type != digest_condition_type:
            raise ValueError(
                f"Cannot create condition with type '{digest_condition_type}' under parent "
                f"with type '{parent.digest_condition_type}'. All conditions in the same tree "
                f"must have the same digest_condition_type."
            )

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = True,
    ) -> "DigestCondition":
        """Create a new DigestCondition with validation."""
        # Validate condition type consistency
        cls._validate_condition_type_consistency(db, data)
        try:
            return super().create(db=db, data=data, check_name=check_name)
        except Exception as e:
            raise ConditionalDependencyError(str(e))

    def update(self, db: Session, *, data: dict[str, Any]) -> "DigestCondition":
        """Update DigestCondition with validation."""
        # Ensure validation data includes current values for fields not being updated
        validation_data = {
            "parent_id": data.get("parent_id", self.parent_id),
            "digest_condition_type": data.get(
                "digest_condition_type", self.digest_condition_type
            ),
        }

        # Validate before updating
        self._validate_condition_type_consistency(db, validation_data)
        return super().update(db=db, data=data)  # type: ignore[return-value]

    def save(self, db: Session) -> "DigestCondition":
        """Save DigestCondition with validation."""
        # Extract current object data for validation
        data = {
            "parent_id": self.parent_id,
            "digest_condition_type": self.digest_condition_type,
        }

        # Validate before saving (only if this has a parent)
        if self.parent_id:
            self._validate_condition_type_consistency(db, data)
        return super().save(db=db)  # type: ignore[return-value]

    @classmethod
    def get_root_condition(
        cls,
        db: Session,
        **kwargs: Any,
    ) -> Optional[Union[ConditionLeaf, ConditionGroup]]:
        """Get the root condition tree for a specific digest condition type.

        Implementation of the abstract base method for DigestCondition's multi-type hierarchy.
        Each digest_config can have separate condition trees for RECEIVER, CONTENT, and PRIORITY
        types. This method retrieves the root of one specific tree.

        Args:
            db: SQLAlchemy database session for querying
            **kwargs: Keyword arguments containing:
                digest_config_id: ID of the digest config
                digest_condition_type: DigestConditionType enum value
                                     Must be one of: RECEIVER, CONTENT, PRIORITY

        Returns:
            Optional[Union[ConditionLeaf, ConditionGroup]]: Root condition tree for the specified
                                                          type, or None if no conditions exist

        Raises:
            ValueError: If required parameters are missing

        Example:
            >>> # Get receiver conditions for a digest
            >>> receiver_conditions = DigestCondition.get_root_condition(
            ...     db, digest_config_id=digest_config.id,
            ...     digest_condition_type=DigestConditionType.RECEIVER
            ... )
            >>> # Get content conditions for the same digest
            >>> content_conditions = DigestCondition.get_root_condition(
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

        root = (
            db.query(cls)
            .filter(
                cls.digest_config_id == digest_config_id,
                cls.digest_condition_type == digest_condition_type,
                cls.parent_id.is_(None),
            )
            .one_or_none()
        )

        if not root:
            return None

        return root.to_correct_condition_type()

    @classmethod
    def get_all_root_conditions(
        cls, db: Session, digest_config_id: str
    ) -> dict[DigestConditionType, Optional[Condition]]:
        """Get root conditions for all digest condition types"""
        return {
            condition_type: cls.get_root_condition(
                db,
                digest_config_id=digest_config_id,
                digest_condition_type=condition_type,
            )
            for condition_type in DigestConditionType
        }
