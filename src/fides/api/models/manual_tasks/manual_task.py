from datetime import datetime, UTC
from typing import Any, Optional, Union
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from pydantic import ConfigDict, create_model, ValidationError
from fides.api.db.base_class import Base
from fides.api.schemas.base_class import FidesSchema
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog, ManualTaskLogStatus
from fides.api.models.manual_tasks.status import StatusType, StatusTransitionMixin
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskType,
    ManualTaskReferenceType,
    ManualTaskFieldType,
    ManualTaskFormField,
    ManualTaskCheckboxField,
    ManualTaskAttachmentField,
)


class ManualTaskInstance(Base, StatusTransitionMixin[StatusType]):
    """Model for tracking task status per entity instance."""
    __tablename__ = "manual_task_instance"

    task_id = Column(String, ForeignKey("manual_task.id"), nullable=False)
    config_id = Column(String, ForeignKey("manual_task_config.id"), nullable=False)
    entity_id = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default=StatusType.pending)
    completed_at = Column(DateTime, nullable=True)
    completed_by_id = Column(String, nullable=True)

    # Relationships
    task = relationship("ManualTask", back_populates="instances")
    config = relationship("ManualTaskConfig", back_populates="instances")
    submissions = relationship("ManualTaskSubmission", back_populates="instance")

    @classmethod
    def create(
        cls,
        db: Session,
        data: dict[str, Any],
    ) -> "ManualTaskInstance":
        """Create a new task instance for an entity.

        Args:
            db: Database session
            data: Dictionary containing task_id, config_id, entity_id, and entity_type
        """
        instance = super().create(
            db=db,
            data=data,
        )
        ManualTaskLog.create_log(
            db=db,
            task_id=data["task_id"],
            config_id=data["config_id"],
            instance_id=instance.id,
            status=ManualTaskLogStatus.complete,
            message=f"Created task instance for {data['entity_type']} {data['entity_id']}",
        )
        return instance

    def get_submissions(self) -> list["ManualTaskSubmission"]:
        """Get all submissions for this instance."""
        return self.submissions


class ManualTask(Base):
    """Model for storing manual tasks.

    This model can be used for both privacy request tasks and general tasks.
    For privacy requests, it replaces the functionality of manual webhooks.
    For other use cases, it provides a flexible task management system.
    """
    __tablename__ = "manual_task"

    task_type = Column(String, nullable=False, default=ManualTaskType.privacy_request)
    parent_entity_id = Column(String, nullable=False)
    parent_entity_type = Column(String, nullable=False)  # Using ManualTaskParentEntityType
    due_date = Column(DateTime, nullable=True)

    # Relationships
    references = relationship("ManualTaskReference", back_populates="task")
    configs = relationship(
        "ManualTaskConfig",
        secondary="manual_task_reference",
        primaryjoin="and_(ManualTask.id == ManualTaskReference.task_id, ManualTaskReference.reference_type == 'manual_task_config')",
        secondaryjoin="ManualTaskConfig.id == ManualTaskReference.reference_id",
        viewonly=True,
    )
    submissions = relationship("ManualTaskSubmission", back_populates="task")
    logs = relationship("ManualTaskLog", back_populates="task")
    instances = relationship("ManualTaskInstance", back_populates="task")

    def get_entity_instances(self, entity_type: str) -> list[ManualTaskInstance]:
        """Get all instances for a specific entity type.

        Args:
            entity_type: Type of entity to get instances for
        """
        return [
            instance for instance in self.instances
            if instance.entity_type == entity_type
        ]

    def get_instance_for_entity(self, entity_id: str, entity_type: str) -> Optional[ManualTaskInstance]:
        """Get the task instance for a specific entity.

        Args:
            entity_id: ID of the entity
            entity_type: Type of the entity
        """
        for instance in self.instances:
            if instance.entity_id == entity_id and instance.entity_type == entity_type:
                return instance
        return None

    def create_manual_task_config(
        self,
        db: Session,
        config_type: str,
        fields: list[Optional[dict[str, Any]]],
    ) -> "ManualTaskConfig":
        """Create a new manual task configuration."""
        config = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": self.id,
                "config_type": config_type,
                "fields": fields,
            }
        )
        ManualTaskLog.create_log(
            db=db,
            task_id=self.id,
            config_id=config.id,
            status=ManualTaskLogStatus.complete,
            message=f"Created manual task configuration for {config_type}",
        )
        return config

    def create_entity_instance(
        self,
        db: Session,
        config_id: str,
        entity_id: str,
        entity_type: str,
    ) -> ManualTaskInstance:
        """Create a new task instance for an entity.

        Args:
            db: Database session
            config_id: ID of the configuration to use
            entity_id: ID of the entity
            entity_type: Type of the entity
        """
        # Create the instance
        instance = ManualTaskInstance.create(
            db=db,
            data={
                "task_id": self.id,
                "config_id": config_id,
                "entity_id": entity_id,
                "entity_type": entity_type,
            }
        )

        # Create a reference to the entity
        ref = ManualTaskReference(
            task_id=self.id,
            reference_id=entity_id,
            reference_type=entity_type
        )
        db.add(ref)
        db.commit()

        return instance

    def get_assigned_user(self) -> Optional[str]:
        """Get the user ID assigned to this task."""
        for ref in self.references:
            if ref.reference_type == ManualTaskReferenceType.assigned_user:
                return ref.reference_id
        return None

    def assign_user(self, db: Session, user_id: str) -> None:
        """Assign a user to this task. This assumes there is a single user assigned to the task.

        Args:
            db: Database session
            user_id: ID of the user to assign
        """
        # Remove any existing user assignment
        for ref in self.references:
            if ref.reference_type == ManualTaskReferenceType.assigned_user:
                db.delete(ref)
                break

        # Create new user assignment
        ref = ManualTaskReference(
            task_id=self.id,
            reference_id=user_id,
            reference_type=ManualTaskReferenceType.assigned_user
        )
        db.add(ref)
        db.commit()

        # Log the user assignment
        ManualTaskLog.create_log(
            db=db,
            task_id=self.id,
            status=ManualTaskLogStatus.complete,
            message=f"User {user_id} assigned to task",
            details={"assigned_user_id": user_id}
        )

    def unassign_user(self, db: Session) -> None:
        """Remove the user assignment from this task.

        Args:
            db: Database session
        """
        for ref in self.references:
            if ref.reference_type == ManualTaskReferenceType.assigned_user:
                user_id = ref.reference_id
                db.delete(ref)
                db.commit()

                # Log the user unassignment
                ManualTaskLog.create_log(
                    db=db,
                    task_id=self.id,
                    status=ManualTaskLogStatus.complete,
                    message=f"User {user_id} unassigned from task",
                    details={"unassigned_user_id": user_id}
                )
                break


class ManualTaskConfig(Base):
    """Model for storing manual task configurations.

    A single configuration may have many fields of different types.
    """
    __tablename__ = "manual_task_config"

    task_id = Column(String, ForeignKey("manual_task.id"), nullable=False)
    config_type = Column(String, nullable=False)  # Using ManualTaskConfigurationType

    # Relationships
    task = relationship("ManualTask", back_populates="configs")
    field_definitions = relationship("ManualTaskConfigField", back_populates="config", cascade="all, delete-orphan")
    submissions = relationship("ManualTaskSubmission", back_populates="config")
    instances = relationship("ManualTaskInstance", back_populates="config")

    @property
    def fields_schema(self) -> FidesSchema:
        """Get the Pydantic model for validating submissions.

        Returns:
            FidesSchema: A Pydantic model for validating submissions
        """
        fields = {}
        for field in self.field_definitions:
            if field.field_type == ManualTaskFieldType.form:
                fields[field.field_key] = (Optional[str], None)
            elif field.field_type == ManualTaskFieldType.checkbox:
                fields[field.field_key] = (Optional[bool], False)
            elif field.field_type == ManualTaskFieldType.attachment:
                fields[field.field_key] = (Optional[dict], None)

        return create_model(  # type: ignore
            __model_name="ManualTaskValidationModel",
            __config__=ConfigDict(extra="forbid"),
            **fields,
        )

    @property
    def fields_non_strict_schema(self) -> FidesSchema:
        """Get the Pydantic model for validating submissions with extra fields allowed.

        Returns:
            FidesSchema: A Pydantic model for validating submissions with extra fields allowed
        """
        fields = {}
        for field in self.field_definitions:
            if field.field_type == ManualTaskFieldType.form:
                fields[field.field_key] = (Optional[str], None)
            elif field.field_type == ManualTaskFieldType.checkbox:
                fields[field.field_key] = (Optional[bool], False)
            elif field.field_type == ManualTaskFieldType.attachment:
                fields[field.field_key] = (Optional[dict], None)

        return create_model(  # type: ignore
            __model_name="ManualTaskValidationModel",
            __config__=ConfigDict(extra="ignore"),
            **fields,
        )

    @property
    def empty_fields_dict(self) -> dict[str, Any]:
        """Return a dictionary that maps defined field keys to their default values.

        Returns:
            dict: Dictionary of field keys to default values
        """
        defaults = {}
        for field in self.field_definitions:
            if field.field_type == ManualTaskFieldType.checkbox:
                defaults[field.field_key] = False
            else:
                defaults[field.field_key] = None
        return defaults

    def add_field(self, field: "ManualTaskConfigField") -> None:
        """Add a field to this configuration.

        Args:
            field: The field to add
        """
        # Validate the field using Pydantic models
        field_model = field._get_field_model()
        field_model.model_validate({
            "field_key": field.field_key,
            "field_type": field.field_type,
            "metadata": field.metadata
        })

        self.field_definitions.append(field)

    def remove_field(self, field_key: str) -> None:
        """Remove a field from this configuration.

        Args:
            field_key: The key of the field to remove
        """
        self.field_definitions = [f for f in self.field_definitions if f.field_key != field_key]

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

    def validate_submission(self, data: dict[str, Any]) -> bool:
        """Validate a submission against all fields in this configuration.

        Args:
            data: The submission data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Validate against the strict schema
            self.fields_schema.model_validate(data)
            return True
        except ValidationError:
            return False

    @classmethod
    def create(cls, db: Session, data: dict[str, Any]) -> "ManualTaskConfig":
        """Create a new manual task configuration."""
        config = super().create(db=db, data=data)
        ManualTaskLog.create_log(
            db=db,
            task_id=data["task_id"],
            config_id=config.id,
            status=ManualTaskLogStatus.complete,
            message=f"Created manual task configuration for {data['config_type']}",
        )
        return config


class ManualTaskReference(Base):
    """Join table to associate manual tasks with multiple references.

    A single task may have many references including privacy requests, configurations, and assigned users.
    """
    __tablename__ = "manual_task_reference"

    task_id = Column(String, ForeignKey("manual_task.id"))
    reference_id = Column(String)
    reference_type = Column(String, nullable=False)

    # Relationships
    task = relationship("ManualTask", back_populates="references")


class ManualTaskConfigField(Base):
    """Model for storing fields associated with each config.

    A single configuration may have many fields of different types.
    """
    __tablename__ = "manual_task_config_field"

    config_id = Column(String, ForeignKey("manual_task_config.id"))
    field_key = Column(String, nullable=False)
    field_type = Column(String, nullable=False)  # Using ManualTaskFieldType
    metadata = Column(JSONB, nullable=False, default={})  # Stores all field metadata

    # Relationships
    config = relationship("ManualTaskConfig", back_populates="field_definitions")
    submissions = relationship("ManualTaskSubmission", back_populates="field")

    __table_args__ = (
        # Add check constraint for field_type
        CheckConstraint(
            "field_type IN ('form', 'checkbox', 'attachment')",
            name="valid_field_type"
        ),
    )

    def validate_field_data(self, data: Any) -> bool:
        """Validate field data using Pydantic models.

        Args:
            data: The data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if self.metadata.get("required", False) and data is None:
                return False

            if data is None:
                return True

            field_model = self._get_field_model()
            field_model.model_validate({
                "field_key": self.field_key,
                "field_type": self.field_type,
                "metadata": self.metadata
            })
            return True
        except ValidationError:
            return False

    def _get_field_model(self) -> Union[ManualTaskFormField, ManualTaskCheckboxField, ManualTaskAttachmentField]:
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
        return self.metadata

    @property
    def label(self) -> str:
        """Get the field label."""
        return self.metadata.get("label", "")

    @property
    def required(self) -> bool:
        """Get whether the field is required."""
        return self.metadata.get("required", False)

    @property
    def help_text(self) -> Optional[str]:
        """Get the help text."""
        return self.metadata.get("help_text")

    def update_metadata(self, metadata: dict[str, Any]) -> None:
        """Update field metadata.

        Args:
            metadata: New metadata to set
        """
        # Validate the metadata before updating
        field_model = self._get_field_model()
        field_model.model_validate({
            "field_key": self.field_key,
            "field_type": self.field_type,
            "metadata": metadata
        })
        self.metadata = metadata

    @classmethod
    def create(cls, db: Session, data: dict[str, Any]) -> "ManualTaskConfigField":
        """Create a new manual task config field."""
        field = super().create(db=db, data=data)
        ManualTaskLog.create_log(
            db=db,
            task_id=data["task_id"],
            config_id=data["config_id"],
            status=ManualTaskLogStatus.complete,
            message=f"Created manual task config field for {data['field_key']}",
        )
        return field


class ManualTaskSubmission(Base):
    """Model for storing user submissions."""
    __tablename__ = "manual_task_submission"

    task_id = Column(String, ForeignKey("manual_task.id"))
    config_id = Column(String, ForeignKey("manual_task_config.id"))
    field_id = Column(String, ForeignKey("manual_task_config_field.id"))
    instance_id = Column(String, ForeignKey("manual_task_instance.id"), nullable=True)
    submitted_by = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, default=datetime.now(UTC))
    data = Column(JSONB, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    completed_by_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")

    # Relationships
    task = relationship("ManualTask", back_populates="submissions")
    config = relationship("ManualTaskConfig", back_populates="submissions")
    field = relationship("ManualTaskConfigField", back_populates="submissions")
    instance = relationship("ManualTaskInstance", back_populates="submissions")

    @classmethod
    def create(cls, db, data) -> "ManualTaskSubmission":
        """Create a new manual task submission."""
        # Validate the submission data
        config = ManualTaskConfig.get(db=db, id=data["config_id"])
        if not config.validate_submission(data["data"]):
            raise ValueError("Invalid submission data")

        submission = super().create(db=db, data=data)
        ManualTaskLog.create_log(
            db=db,
            task_id=data["task_id"],
            config_id=data["config_id"],
            instance_id=data["instance_id"],
            status=ManualTaskLogStatus.complete,
            message=f"Created manual task submission for {data['field_id']}",
        )
        return submission
