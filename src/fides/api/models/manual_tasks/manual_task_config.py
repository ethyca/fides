from typing import Any, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, relationship
from sqlalchemy.orm import declared_attr

from fides.api.db.base_class import Base
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskConfigurationType,
    ManualTaskFieldMetadata,
)

if TYPE_CHECKING:
    from fides.api.models.manual_tasks.manual_task import ManualTask
    from fides.api.models.manual_tasks.manual_task_log import ManualTaskLogStatus


class ManualTaskConfig(Base):
    """Model for storing manual task configurations.
    A single configuration may have many fields of different types.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "manual_task_config"

    task_id = Column(String, ForeignKey("manual_task.id"), nullable=False)
    config_type = Column(String, nullable=False)  # Using ManualTaskConfigurationType
    version = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, nullable=False, default=True)

    # Relationships
    task = relationship("ManualTask", back_populates="configs")
    field_definitions = relationship(
        "ManualTaskConfigField", back_populates="config", cascade="all, delete-orphan"
    )
    logs = relationship(
        "ManualTaskLog",
        back_populates="config",
        primaryjoin="ManualTaskConfig.id == ManualTaskLog.config_id",
        viewonly=True,
    )

    __table_args__ = (
        # Add check constraint for config_type
        CheckConstraint(
            "config_type IN ('access_privacy_request', 'erasure_privacy_request')",
            name="valid_config_type",
        ),
    )

    @classmethod
    def create(
        cls, db: Session, *, data: dict[str, Any], check_name: bool = True
    ) -> "ManualTaskConfig":
        """Create a new manual task configuration."""
        # Validate config_type
        try:
            ManualTaskConfigurationType(data["config_type"])
        except ValueError:
            raise ValueError(f"Invalid config type: {data['config_type']}")

        config = super().create(db=db, data=data, check_name=check_name)

        # Log the config creation as a task-level log
        ManualTaskLog.create_log(
            db=db,
            task_id=data["task_id"],
            config_id=config.id,
            status=ManualTaskLogStatus.created,
            message=f"Created manual task configuration for {data['config_type']}",
            details={
                "config_type": data["config_type"],
            },
        )
        return config

    def get_field(self, field_key: str) -> Optional["ManualTaskConfigField"]:
        """Get a field by its key."""
        for field in self.field_definitions:
            if field.field_key == field_key:
                return field
        return None


class ManualTaskConfigField(Base):
    """Model for storing fields associated with each config."""

    @declared_attr
    def __tablename__(cls) -> str:
        return "manual_task_config_field"

    task_id = Column(String, ForeignKey("manual_task.id"), nullable=False)
    config_id = Column(String, ForeignKey("manual_task_config.id"))
    field_key = Column(String, nullable=False)
    field_type = Column(String, nullable=False)  # Using ManualTaskFieldType
    field_metadata = Column(JSONB, nullable=False, default={})

    # Relationships
    config = relationship("ManualTaskConfig", back_populates="field_definitions")

    __table_args__ = (
        # Add check constraint for field_type
        CheckConstraint(
            "field_type IN ('text', 'checkbox', 'attachment')", name="valid_field_type"
        ),
        CheckConstraint("field_key IS NOT NULL", name="valid_field_key"),
    )

    @property
    def field_metadata_model(self) -> ManualTaskFieldMetadata:
        """Get the field metadata as a Pydantic model."""
        return ManualTaskFieldMetadata.model_validate(self.field_metadata)

    @classmethod
    def create(
        cls, db: Session, *, data: dict[str, Any], check_name: bool = True
    ) -> "ManualTaskConfigField":
        """Create a new manual task config field."""
        # Create the field and let SQLAlchemy complex type validation handled in service.
        field = super().create(db=db, data=data, check_name=check_name)

        # Get the config to access its task_id
        config = (
            db.query(ManualTaskConfig)
            .filter(ManualTaskConfig.id == data["config_id"])
            .first()
        )

        # Create a log entry
        ManualTaskLog.create_log(
            db=db,
            task_id=config.task_id if config else None,
            config_id=data["config_id"],
            status=ManualTaskLogStatus.created,
            message=f"Created manual task config field for {data['field_key']}",
        )
        return field
