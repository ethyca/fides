from typing import Any, List, Optional, Union

from pydantic import ConfigDict, ValidationError, create_model
from sqlalchemy import select
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
)
from fides.api.models.manual_tasks.manual_task_log import (
    ManualTaskLog,
    ManualTaskLogStatus,
)
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskAttachmentField,
    ManualTaskCheckboxField,
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskFormField,
    ManualTaskParentEntityType,
    ManualTaskType,
)


class ManualTaskService:
    def __init__(self, db: Session):
        self.db = db

    def get_task_by_parent_entity_id(
        self,
        parent_entity_id: str,
        parent_entity_type: ManualTaskParentEntityType,
        task_type: ManualTaskType,
    ) -> Optional[ManualTask]:
        """Get the manual task for a specific connection.

        Args:
            parent_entity_id: The parent entity ID
            parent_entity_type: The parent entity type
            task_type: The task type

        Returns:
            Optional[ManualTask]: The manual task for the connection, if it exists
        """
        query = select(ManualTask).where(
            ManualTask.parent_entity_type == parent_entity_type,
            ManualTask.parent_entity_id == parent_entity_id,
            ManualTask.task_type == task_type,
        )
        return self.db.execute(query).scalar_one_or_none()

    def get_configs_by_parent_entity_id(
        self,
        parent_entity_id: str,
        parent_entity_type: ManualTaskParentEntityType,
        task_type: ManualTaskType,
    ) -> List[ManualTaskConfig]:
        """Get all task configurations for a specific connection.

        Args:
            parent_entity_id: The parent entity ID
            parent_entity_type: The parent entity type
            task_type: The task type

        Returns:
            List[ManualTaskConfig]: List of task configurations for the connection
        """
        task = self.get_task_by_parent_entity_id(
            parent_entity_id, parent_entity_type, task_type
        )
        if not task:
            return []
        return task.configs

    def get_field(
        self, config: ManualTaskConfig, field_key: str
    ) -> Optional[ManualTaskConfigField]:
        """Get a field by its key.

        Args:
            config: The manual task configuration
            field_key: The key of the field to get

        Returns:
            Optional[ManualTaskConfigField]: The field if found, None otherwise
        """
        for field in config.field_definitions:
            if field.field_key == field_key:
                return field
        return None

    def to_config_response(self, config: ManualTaskConfig) -> dict:
        """Convert a task configuration to a response.

        Args:
            config: The manual task configuration

        Returns:
            dict: Configuration response in the required format
        """
        # Map config type to request type
        request_type = (
            "access"
            if config.config_type == ManualTaskConfigurationType.access_privacy_request
            else "erasure"
        )

        # Get input types from field definitions
        input_types = set()
        for field in config.field_definitions:
            if field.field_type == "form":
                input_types.add("string")
            elif field.field_type == "attachment":
                input_types.add("file")
            elif field.field_type == "checkbox":
                input_types.add("checkbox")

        return {
            "task_config_id": config.id,
            "name": config.config_type,
            "description": f"Manual task configuration for {config.config_type}",
            "input_type": list(input_types),
            "request_type": [request_type],
            "assignedTo": config.task.assigned_users,
        }

    def create_or_get_task(
        self,
        parent_entity_id: str,
        parent_entity_type: ManualTaskParentEntityType,
        task_type: ManualTaskType,
    ) -> ManualTask:
        """Get existing task or create a new one for a connection.

        Args:
            parent_entity_id: The parent entity ID
            parent_entity_type: The parent entity type
            task_type: The task type

        Returns:
            ManualTask: The task for the connection
        """
        task = self.get_task_by_parent_entity_id(
            parent_entity_id, parent_entity_type, task_type
        )
        if not task:
            task = ManualTask.create(
                db=self.db,
                data={
                    "task_type": task_type,
                    "parent_entity_id": parent_entity_id,
                    "parent_entity_type": parent_entity_type,
                },
            )
        return task

    def create_or_update_task_config(
        self,
        task: ManualTask,
        config_type: str,
        fields: Optional[List[dict]] = None,
    ) -> ManualTaskConfig:
        """Create or update a task configuration.

        Args:
            task: The task
            config_type: Type of configuration to create or update
            fields: Optional list of field definitions

        Returns:
            ManualTaskConfig: The created or updated configuration
        """
        try:
            return task.create_manual_task_config(
                db=self.db,
                config_type=config_type,
                fields=fields or [],
            )
        except ValueError as e:
            if "already exists" in str(e):
                return task.update_task_config(
                    db=self.db,
                    config_type=config_type,
                    fields=fields,
                )
            raise

    def delete_task_config(self, task: ManualTask, task_config_id: str) -> None:
        """Delete a task configuration.

        Args:
            task: The task
            task_config_id: ID of the configuration to delete

        Raises:
            ValueError: If config_type is invalid or if no config exists
        """
        config = task.get_task_config_by_id(task_config_id)
        if not config:
            raise ValueError(
                f"No configuration with ID {task_config_id} exists for this connection"
            )

        # Delete the configuration
        config.delete(self.db)

    def get_config_schema(
        self, config: ManualTaskConfig, strict: bool = True
    ) -> FidesSchema:
        """Get the Pydantic model for validating submissions.

        Args:
            config: The manual task configuration
            strict: Whether to use strict validation (no extra fields allowed)

        Returns:
            FidesSchema: A Pydantic model for validating submissions
        """
        fields = {}
        for field in config.field_definitions:
            if field.field_type == ManualTaskFieldType.form:
                fields[field.field_key] = (Optional[str], None)
            elif field.field_type == ManualTaskFieldType.checkbox:
                fields[field.field_key] = (Optional[bool], False)
            elif field.field_type == ManualTaskFieldType.attachment:
                fields[field.field_key] = (Optional[dict], None)

        return create_model(  # type: ignore
            __model_name="ManualTaskValidationModel",
            __config__=ConfigDict(extra="forbid" if strict else "ignore"),
            **fields,
        )

    def validate_submission(
        self,
        config: ManualTaskConfig,
        data: dict[str, Any],
        field_id: Optional[str] = None,
    ) -> bool:
        """Validate a submission against all fields in this configuration.

        Args:
            config: The manual task configuration
            data: The submission data to validate
            field_id: Optional ID of the field being submitted. If provided, only validates that field.

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # If field_id is provided, only validate that field
            if field_id:
                field = next(
                    (f for f in config.field_definitions if f.id == field_id), None
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
                self.get_config_schema(config, strict=False).model_validate(field_data)
                return True

            # Otherwise validate all fields
            for field in config.field_definitions:
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
            self.get_config_schema(config, strict=True).model_validate(data)
            return True
        except ValidationError:
            return False

    def add_field_to_config(
        self, config: ManualTaskConfig, field_data: dict[str, Any]
    ) -> ManualTaskConfigField:
        """Add a field to a configuration.

        Args:
            config: The configuration to add the field to
            field_data: The field data to add

        Returns:
            ManualTaskConfigField: The created field
        """
        # Create the field
        field = ManualTaskConfigField.create(
            db=self.db,
            data={
                "task_id": config.task_id,
                "config_id": config.id,
                **field_data,
            },
        )

        # Add to config
        config.field_definitions.append(field)
        self.db.commit()

        # Log the field addition
        ManualTaskLog.create_log(
            db=self.db,
            task_id=config.task_id,
            config_id=config.id,
            status=ManualTaskLogStatus.complete,
            message=f"Added field {field.field_key} to configuration",
            details={
                "field_key": field.field_key,
                "field_type": field.field_type,
                "field_metadata": field.field_metadata,
            },
        )

        return field

    def remove_field_from_config(
        self, config: ManualTaskConfig, field_key: str
    ) -> None:
        """Remove a field from a configuration.

        Args:
            config: The configuration to remove the field from
            field_key: The key of the field to remove
        """
        # Find the field before removing it
        field = self.get_field(config, field_key)
        if field:
            # Log the field removal
            ManualTaskLog.create_log(
                db=self.db,
                task_id=config.task_id,
                config_id=config.id,
                status=ManualTaskLogStatus.complete,
                message=f"Removed field {field_key} from configuration",
                details={
                    "field_key": field_key,
                    "field_type": field.field_type,
                    "field_metadata": field.field_metadata,
                },
            )

        # Remove the field
        config.field_definitions = [
            f for f in config.field_definitions if f.field_key != field_key
        ]
        self.db.commit()
