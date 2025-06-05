from datetime import datetime, timezone
from typing import Any, Optional, Union

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.manual_tasks.manual_task_log import (
    ManualTaskLog,
    ManualTaskLogStatus,
)
from fides.api.models.manual_tasks.status import StatusType
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskAttachmentField,
    ManualTaskCheckboxField,
    ManualTaskFieldType,
    ManualTaskFormField,
)


class ManualTaskConfig(Base):
    """Model for storing manual task configurations.

    A single configuration may have many fields of different types.
    """

    __tablename__ = "manual_task_config"

    task_id = Column(String, ForeignKey("manual_task.id"), nullable=False)
    config_type = Column(String, nullable=False)  # Using ManualTaskConfigurationType

    # Relationships
    task = relationship("ManualTask", back_populates="configs")
    field_definitions = relationship(
        "ManualTaskConfigField", back_populates="config", cascade="all, delete-orphan"
    )
    submissions = relationship("ManualTaskSubmission", back_populates="config")
    instances = relationship("ManualTaskInstance", back_populates="config")
    logs = relationship(
        "ManualTaskLog",
        back_populates="config",
        primaryjoin="and_(ManualTaskConfig.id == ManualTaskLog.config_id, ManualTaskLog.instance_id.is_(None))",
        viewonly=True,
    )

    @classmethod
    def create(cls, db: Session, data: dict[str, Any]) -> "ManualTaskConfig":
        """Create a new manual task configuration."""
        # Extract fields from data
        fields = data.pop("fields", [])

        # Create the config without fields
        config = super().create(db=db, data=data)

        # Add fields if provided
        if fields:
            for field_data in fields:
                field = ManualTaskConfigField.create(
                    db=db,
                    data={
                        "task_id": config.task_id,
                        "config_id": config.id,
                        **field_data,
                    },
                )
                config.field_definitions.append(field)
            db.commit()

        # Log the config creation as a task-level log
        ManualTaskLog.create_log(
            db=db,
            task_id=data["task_id"],
            config_id=config.id,
            status=ManualTaskLogStatus.complete,
            message=f"Created manual task configuration for {data['config_type']}",
            details={
                "config_type": data["config_type"],
                "fields": fields,
            },
        )
        return config

    def delete(self, db: Session) -> None:
        """Delete this configuration.

        Args:
            db: Database session

        Raises:
            ValueError: If there are active instances using this configuration
        """
        # Check for active instances
        active_instances = [
            instance
            for instance in self.instances
            if instance.status != StatusType.completed
        ]

        if active_instances:
            # Log the attempt to delete with active instances
            ManualTaskLog.create_log(
                db=db,
                task_id=self.task_id,
                config_id=self.id,
                status=ManualTaskLogStatus.paused,
                message="Cannot delete configuration with active instances",
                details={
                    "active_instance_count": len(active_instances),
                    "instance_ids": [instance.id for instance in active_instances],
                },
            )
            raise ValueError(
                f"Cannot delete configuration with {len(active_instances)} active instances"
            )

        # Log the deletion
        ManualTaskLog.create_log(
            db=db,
            task_id=self.task_id,
            config_id=self.id,
            status=ManualTaskLogStatus.complete,
            message=f"Deleted manual task configuration for {self.config_type}",
        )

        # Delete the configuration
        super().delete(db)

    # Configuration Management
    @classmethod
    def get_by_type(
        cls, db: Session, task_id: str, config_type: str
    ) -> Optional["ManualTaskConfig"]:
        """Get a specific task configuration by type.

        Args:
            db: Database session
            task_id: ID of the task
            config_type: Type of configuration to get

        Returns:
            Optional[ManualTaskConfig]: The configuration if it exists
        """
        return db.query(cls).filter_by(task_id=task_id, config_type=config_type).first()

    @classmethod
    def get_by_id(
        cls, db: Session, task_id: str, task_config_id: str
    ) -> Optional["ManualTaskConfig"]:
        """Get a specific task configuration by ID.

        Args:
            db: Database session
            task_id: ID of the task
            task_config_id: ID of the configuration to get

        Returns:
            Optional[ManualTaskConfig]: The configuration if it exists
        """
        return db.query(cls).filter_by(task_id=task_id, id=task_config_id).first()

    @classmethod
    def create_for_task(
        cls,
        db: Session,
        task_id: str,
        config_type: str,
        fields: list[Optional[dict[str, Any]]],
    ) -> "ManualTaskConfig":
        """Create a new manual task configuration for a task.

        Args:
            db: Database session
            task_id: ID of the task
            config_type: Type of configuration to create
            fields: List of field definitions

        Returns:
            ManualTaskConfig: The created configuration
        """
        config = cls.create(
            db=db,
            data={
                "task_id": task_id,
                "config_type": config_type,
                "fields": fields,
            },
        )
        ManualTaskLog.create_log(
            db=db,
            task_id=task_id,
            config_id=config.id,
            status=ManualTaskLogStatus.complete,
            message=f"Created manual task configuration for {config_type}",
        )
        return config

    def update(
        self,
        db: Session,
        data: dict[str, Any],
    ) -> "ManualTaskConfig":
        """Update the configuration.

        Args:
            db: Database session
            data: Dictionary containing fields to update

        Returns:
            ManualTaskConfig: The updated configuration
        """
        # Update fields if provided
        if "fields" in data:
            # Remove existing fields
            for field in self.field_definitions:
                db.delete(field)
            self.field_definitions = []
            db.commit()

            # Add new fields
            for field_data in data["fields"]:
                field = ManualTaskConfigField.create(
                    db=db,
                    data={
                        "task_id": self.task_id,
                        "config_id": self.id,
                        **field_data,
                    },
                )
                self.field_definitions.append(field)
            db.commit()

        # Log the update
        ManualTaskLog.create_log(
            db=db,
            task_id=self.task_id,
            config_id=self.id,
            status=ManualTaskLogStatus.complete,
            message=f"Updated manual task configuration for {self.config_type}",
            details={
                "config_type": self.config_type,
                "fields": data.get("fields", []),
            },
        )

        return self

    def get_field(self, field_key: str) -> Optional["ManualTaskConfigField"]:
        """Get a field by its key.

        Args:
            field_key: The key of the field to get

        Returns:
            Optional[ManualTaskConfigField]: The field if found, None otherwise
        """
        for field in self.field_definitions:
            if field.field_key == field_key:
                return field
        return None


class ManualTaskConfigField(Base):
    """Model for storing fields associated with each config.

    A single configuration may have many fields of different types.
    """

    __tablename__ = "manual_task_config_field"

    task_id = Column(String, ForeignKey("manual_task.id"), nullable=False)
    config_id = Column(String, ForeignKey("manual_task_config.id"))
    field_key = Column(String, nullable=False)
    field_type = Column(String, nullable=False)  # Using ManualTaskFieldType
    field_metadata = Column(
        JSONB, nullable=False, default={}
    )  # Stores all field metadata

    # Relationships
    task = relationship("ManualTask", back_populates="field_definitions")
    config = relationship("ManualTaskConfig", back_populates="field_definitions")
    submissions = relationship("ManualTaskSubmission", back_populates="field")

    __table_args__ = (
        # Add check constraint for field_type
        CheckConstraint(
            "field_type IN ('form', 'checkbox', 'attachment')", name="valid_field_type"
        ),
    )

    @property
    def label(self) -> str:
        """Get the field label."""
        return self.field_metadata.get("label", "")

    @property
    def required(self) -> bool:
        """Get whether the field is required."""
        return self.field_metadata.get("required", False)

    @property
    def help_text(self) -> Optional[str]:
        """Get the help text."""
        return self.field_metadata.get("help_text")

    def _get_field_model(
        self,
    ) -> Union[ManualTaskFormField, ManualTaskCheckboxField, ManualTaskAttachmentField]:
        """Get the appropriate Pydantic model for this field type.

        Returns:
            Union[ManualTaskFormField, ManualTaskCheckboxField, ManualTaskAttachmentField]: The appropriate field model
        """
        if self.field_type == ManualTaskFieldType.form:
            return ManualTaskFormField
        elif self.field_type == ManualTaskFieldType.checkbox:
            return ManualTaskCheckboxField
        elif self.field_type == ManualTaskFieldType.attachment:
            return ManualTaskAttachmentField
        raise ValueError(f"Invalid field type: {self.field_type}")

    def get_field_metadata(self) -> dict[str, Any]:
        """Get field metadata in a format compatible with the schema.

        Returns:
            dict: Field metadata
        """
        return self.field_metadata

    def update_metadata(self, metadata: dict[str, Any]) -> None:
        """Update field metadata.

        Args:
            metadata: New metadata to set
        """
        # Validate the metadata before updating
        field_model = self._get_field_model()
        field_model.model_validate(
            {
                "field_key": self.field_key,
                "field_type": self.field_type,
                "field_metadata": metadata,
            }
        )
        self.field_metadata = metadata

    @classmethod
    def create(cls, db: Session, data: dict[str, Any]) -> "ManualTaskConfigField":
        """Create a new manual task config field."""
        # Validate field metadata
        if "field_metadata" not in data:
            raise ValueError("Field metadata is required")

        # Validate field type
        if data["field_type"] not in ["form", "checkbox", "attachment"]:
            raise ValueError("Invalid field type")

        field = super().create(db=db, data=data)
        # Get the config to access its task_id
        config = (
            db.query(ManualTaskConfig)
            .filter(ManualTaskConfig.id == data["config_id"])
            .first()
        )
        ManualTaskLog.create_log(
            db=db,
            task_id=config.task_id if config else None,
            config_id=data["config_id"],
            status=ManualTaskLogStatus.complete,
            message=f"Created manual task config field for {data['field_key']}",
        )
        return field


class ManualTaskSubmission(Base):
    """Model for storing user submissions.

    Each submission represents data for a single field.
    """

    # 1. Table Definition
    __tablename__ = "manual_task_submission"
    task_id = Column(String, ForeignKey("manual_task.id"))
    config_id = Column(String, ForeignKey("manual_task_config.id"))
    field_id = Column(String, ForeignKey("manual_task_config_field.id"))
    instance_id = Column(String, ForeignKey("manual_task_instance.id"), nullable=True)
    submitted_by = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, default=datetime.now(timezone.utc))
    data = Column(JSONB, nullable=False)

    # 2. Relationships
    task = relationship("ManualTask", back_populates="submissions")
    config = relationship("ManualTaskConfig", back_populates="submissions")
    field = relationship("ManualTaskConfigField", back_populates="submissions")
    instance = relationship("ManualTaskInstance", back_populates="submissions")

    # 3. CRUD Operations
    @classmethod
    def create(
        cls, db: Session, data: dict[str, Any], check_name: Optional[bool]
    ) -> None:
        """Create a new submission for a single field."""
        # Validate that data contains only one field
        if len(data["data"]) != 1:
            raise ValueError("Submission must contain data for exactly one field")

        # Get the field being submitted
        field = ManualTaskConfigField.get_by_key_or_id(
            db=db, data={"id": data["field_id"]}
        )
        if not field:
            raise ValueError(f"No field found with ID {data['field_id']}")

        # Validate that the data is for the correct field
        field_key = next(iter(data["data"].keys()))
        if field_key != field.field_key:
            raise ValueError(f"Data must be for field {field.field_key}")

        return super().create(db=db, data=data, check_name=check_name)

    @classmethod
    def create_or_update(
        cls, db: Session, *, data: dict[str, Any], check_name: Optional[bool] = True
    ) -> "ManualTaskSubmission":
        """Create or update a submission for a single field."""
        try:
            # Validate that data contains only one field
            if len(data["data"]) != 1:
                raise ValueError("Submission must contain data for exactly one field")

            # Get the field being submitted
            field = ManualTaskConfigField.get_by_key_or_id(
                db=db, data={"id": data["field_id"]}
            )
            if not field:
                raise ValueError(f"No field found with ID {data['field_id']}")

            # Validate that the data is for the correct field
            field_key = next(iter(data["data"].keys()))
            if field_key != field.field_key:
                raise ValueError(f"Data must be for field {field.field_key}")

            # Check if instance is completed
            if data.get("instance_id"):
                # Query instance status directly without importing ManualTaskInstance
                instance_status = db.execute(
                    "SELECT status FROM manual_task_instance WHERE id = :instance_id",
                    {"instance_id": data["instance_id"]},
                ).scalar()

                if instance_status == StatusType.completed:
                    # Log error for completed task
                    ManualTaskLog.create_log(
                        db=db,
                        task_id=data["task_id"],
                        config_id=data["config_id"],
                        instance_id=data["instance_id"],
                        status=ManualTaskLogStatus.error,
                        message="Cannot submit to a completed task instance",
                        details={
                            "field_key": field_key,
                            "field_type": field.field_type,
                            "submitted_by": data["submitted_by"],
                        },
                    )
                    return None

            submission = super().create_or_update(
                db=db, data=data, check_name=check_name
            )

            # Update instance status based on submissions
            if submission.instance:
                submission.instance.update_status_from_submissions(db)

            # Get instance status after update
            instance_status = (
                db.execute(
                    "SELECT status FROM manual_task_instance WHERE id = :instance_id",
                    {"instance_id": data["instance_id"]},
                ).scalar()
                if data.get("instance_id")
                else None
            )

            # Log submission creation/update
            ManualTaskLog.create_log(
                db=db,
                task_id=data["task_id"],
                config_id=data["config_id"],
                instance_id=data["instance_id"],
                status=ManualTaskLogStatus.complete,
                message=f"Created submission for field {field_key}",
                details={
                    "field_key": field_key,
                    "field_type": field.field_type,
                    "submitted_by": data["submitted_by"],
                    "status": instance_status,
                },
            )

            return submission
        except ValueError as e:
            # Create error log for validation failures
            ManualTaskLog.create_log(
                db=db,
                task_id=data["task_id"],
                config_id=data["config_id"],
                instance_id=data.get("instance_id"),
                status=ManualTaskLogStatus.error,
                message=f"Invalid field data: {str(e)}",
                details={
                    "error": str(e),
                    "field_id": data.get("field_id"),
                    "submitted_by": data.get("submitted_by"),
                },
            )
            raise
