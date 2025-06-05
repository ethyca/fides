from typing import Any, Optional, Union

from pydantic import ConfigDict, ValidationError, create_model
from sqlalchemy import CheckConstraint, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.manual_tasks.manual_task_log import (
    ManualTaskLog,
    ManualTaskLogStatus,
)
from fides.api.models.manual_tasks.status import StatusType
from fides.api.schemas.base_class import FidesSchema
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
        # Set the task_id from the config
        field.task_id = self.task_id

        # Validate the field using Pydantic models
        field_model = field._get_field_model()
        field_model.model_validate(
            {
                "field_key": field.field_key,
                "field_type": field.field_type,
                "field_metadata": field.field_metadata,
            }
        )

        self.field_definitions.append(field)

        # Log the field addition as a task-level log
        ManualTaskLog.create_log(
            db=field._sa_instance_state.session,
            task_id=self.task_id,
            config_id=self.id,
            status=ManualTaskLogStatus.complete,
            message=f"Added field {field.field_key} to configuration",
            details={
                "field_key": field.field_key,
                "field_type": field.field_type,
                "field_metadata": field.field_metadata,
            },
        )

    def remove_field(self, field_key: str) -> None:
        """Remove a field from this configuration.

        Args:
            field_key: The key of the field to remove
        """
        # Find the field before removing it
        field = self.get_field(field_key)
        if field:
            # Log the field removal as a task-level log
            ManualTaskLog.create_log(
                db=field._sa_instance_state.session,
                task_id=self.task_id,
                config_id=self.id,
                status=ManualTaskLogStatus.complete,
                message=f"Removed field {field_key} from configuration",
                details={
                    "field_key": field_key,
                    "field_type": field.field_type,
                    "field_metadata": field.field_metadata,
                },
            )

        self.field_definitions = [
            f for f in self.field_definitions if f.field_key != field_key
        ]

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

    def validate_submission(
        self, data: dict[str, Any], field_id: Optional[str] = None
    ) -> bool:
        """Validate a submission against all fields in this configuration.

        Args:
            data: The submission data to validate
            field_id: Optional ID of the field being submitted. If provided, only validates that field.

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # If field_id is provided, only validate that field
            if field_id:
                field = next(
                    (f for f in self.field_definitions if f.id == field_id), None
                )
                if not field:
                    return False

                # For required fields, ensure the data is present and valid
                if field.required and field.field_key not in data:
                    return False

                # Validate the field data
                if field.field_type == ManualTaskFieldType.attachment:
                    attachment_data = data.get(field.field_key)
                    if attachment_data is not None:
                        # Check required attachment_ids
                        if "attachment_ids" not in attachment_data:
                            return False

                        # Check file type
                        if "filename" in attachment_data:
                            file_extension = (
                                attachment_data["filename"].split(".")[-1].lower()
                            )
                            allowed_types = field.field_metadata.get("file_types", [])
                            if allowed_types and file_extension not in allowed_types:
                                return False

                        # Check file size
                        if "size" in attachment_data:
                            max_size = field.field_metadata.get("max_file_size")
                            if max_size and attachment_data["size"] > max_size:
                                return False

                        # Check number of files
                        if field.field_metadata.get("multiple", False):
                            max_files = field.field_metadata.get("max_files")
                            if (
                                max_files
                                and len(attachment_data["attachment_ids"]) > max_files
                            ):
                                return False

                # Validate against the non-strict schema for single field
                field_data = {field.field_key: data.get(field.field_key)}
                self.fields_non_strict_schema.model_validate(field_data)
                return True

            # Otherwise validate all fields (for backward compatibility)
            for field in self.field_definitions:
                if field.required and field.field_key not in data:
                    return False

                # Check attachment fields for required attachment_ids
                if (
                    field.field_type == ManualTaskFieldType.attachment
                    and field.field_metadata.get("require_attachment_id", True)
                    and data.get(field.field_key) is not None
                ):
                    attachment_data = data[field.field_key]
                    if "attachment_ids" not in attachment_data:
                        return False

                    # Check file type
                    if "filename" in attachment_data:
                        file_extension = (
                            attachment_data["filename"].split(".")[-1].lower()
                        )
                        allowed_types = field.field_metadata.get("file_types", [])
                        if allowed_types and file_extension not in allowed_types:
                            return False

                    # Check file size
                    if "size" in attachment_data:
                        max_size = field.field_metadata.get("max_file_size")
                        if max_size and attachment_data["size"] > max_size:
                            return False

                    # Check number of files
                    if field.field_metadata.get("multiple", False):
                        max_files = field.field_metadata.get("max_files")
                        if (
                            max_files
                            and len(attachment_data["attachment_ids"]) > max_files
                        ):
                            return False

            # Then validate against the strict schema
            self.fields_schema.model_validate(data)
            return True
        except ValidationError:
            return False

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

    def validate_field_data(self, data: Any) -> bool:
        """Validate field data using Pydantic models.

        Args:
            data: The data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if self.field_metadata.get("required", False) and data is None:
                return False

            if data is None:
                return True

            # Validate based on field type
            if self.field_type == ManualTaskFieldType.form:
                return isinstance(data, str)
            elif self.field_type == ManualTaskFieldType.checkbox:
                return isinstance(data, bool)
            elif self.field_type == ManualTaskFieldType.attachment:
                if not isinstance(data, dict):
                    return False
                if self.field_metadata.get("require_attachment_id", True):
                    return "attachment_ids" in data
                return True
            return False
        except Exception:
            return False

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
