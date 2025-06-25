from typing import TYPE_CHECKING, Any, Optional, cast

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func

from fides.api.db.base_class import Base, FidesBase
from fides.api.db.util import EnumColumn
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskConfigurationType,
    ManualTaskFieldMetadata,
    ManualTaskFieldType,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskExecutionTiming,
    ManualTaskLogStatus,
)

if TYPE_CHECKING:  # pragma: no cover
    from fides.api.models.manual_tasks.manual_task import ManualTask  # pragma: no cover
    from fides.api.models.manual_tasks.manual_task_instance import (
        ManualTaskInstance,  # pragma: no cover
    )
    from fides.api.models.manual_tasks.manual_task_instance import (
        ManualTaskSubmission,  # pragma: no cover
    )


class ManualTaskConfig(Base):
    """Model for storing manual task configurations.
    A single configuration may have many fields of different types.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        return "manual_task_config"

    # redefined here because there's a minor, unintended discrepancy between
    # this `id` field and that of the `Base` class, which explicitly sets `index=True`.
    # TODO: we likely should _not_ be setting `index=True` on the `id`
    # attribute of the `Base` class, as `primary_key=True` already specifies a
    # primary key constraint, which will implicitly create an index for the field.
    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    task_id = Column(
        String,
        ForeignKey(
            "manual_task.id",
            name="manual_task_config_task_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    config_type = Column(EnumColumn(ManualTaskConfigurationType), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, nullable=False, default=True)
    execution_timing = Column(
        EnumColumn(ManualTaskExecutionTiming),
        nullable=False,
        default=ManualTaskExecutionTiming.pre_execution,
    )

    __table_args__ = (
        Index("ix_manual_task_config_config_type", "config_type"),
        Index("ix_manual_task_config_task_id", "task_id"),
    )

    # Relationships
    task = relationship("ManualTask", back_populates="configs", viewonly=True)
    instances = relationship(
        "ManualTaskInstance", back_populates="config", uselist=True, viewonly=True
    )
    submissions = relationship(
        "ManualTaskSubmission", back_populates="config", uselist=True, viewonly=True
    )
    field_definitions = relationship(
        "ManualTaskConfigField",
        back_populates="config",
        cascade="all, delete-orphan",
        uselist=True,
    )
    logs = relationship(
        "ManualTaskLog",
        back_populates="config",
        primaryjoin="ManualTaskConfig.id == ManualTaskLog.config_id",
        cascade="all, delete-orphan",
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

    # redefined here because there's a minor, unintended discrepancy between
    # this `id` field and that of the `Base` class, which explicitly sets `index=True`.
    # TODO: we likely should _not_ be setting `index=True` on the `id`
    # attribute of the `Base` class, as `primary_key=True` already specifies a
    # primary key constraint, which will implicitly create an index for the field.
    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    task_id = Column(
        String,
        ForeignKey(
            "manual_task.id",
            name="manual_task_config_field_task_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    config_id = Column(
        String,
        ForeignKey(
            "manual_task_config.id",
            name="manual_task_config_field_config_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    field_key = Column(String, nullable=False)
    field_type = Column(
        EnumColumn(ManualTaskFieldType), nullable=False
    )  # Using ManualTaskFieldType
    field_metadata: dict[str, Any] = cast(
        dict[str, Any], Column(JSONB, nullable=False, default={})
    )

    __table_args__ = (
        UniqueConstraint("config_id", "field_key", name="unique_field_key_per_config"),
        Index("ix_manual_task_config_field_config_id", "config_id"),
        Index("ix_manual_task_config_field_field_key", "field_key"),
        Index("ix_manual_task_config_field_task_id", "task_id"),
    )

    # Relationships
    config = relationship(
        "ManualTaskConfig", back_populates="field_definitions", viewonly=True
    )
    submissions = relationship(
        "ManualTaskSubmission",
        back_populates="field",
        uselist=True,
        cascade="all, delete-orphan",
    )

    @property
    def field_metadata_model(self) -> ManualTaskFieldMetadata:
        """Get the field metadata as a Pydantic model."""
        assert isinstance(
            self.field_metadata, dict
        ), "field_metadata must be a dictionary"
        return ManualTaskFieldMetadata.model_validate(self.field_metadata)

    @classmethod
    def create(
        cls, db: Session, *, data: dict[str, Any], check_name: bool = True
    ) -> "ManualTaskConfigField":
        """Create a new manual task config field."""
        # Get the config to access its task_id and check if it exists
        try:
            config = (
                db.query(ManualTaskConfig)
                .filter(ManualTaskConfig.id == data["config_id"])
                .first()
            )
            if not config:
                raise ValueError(f"Config with id {data['config_id']} not found")
        except Exception as e:
            raise ValueError(f"Config with id {data['config_id']} not found: {e}")

        # Create the field and let SQLAlchemy complex type validation handled in service.
        field = super().create(db=db, data=data, check_name=check_name)

        # Create a log entry
        ManualTaskLog.create_log(
            db=db,
            task_id=config.task_id,
            config_id=data["config_id"],
            status=ManualTaskLogStatus.created,
            message=f"Created manual task config field for {data['field_key']}",
        )
        return field
