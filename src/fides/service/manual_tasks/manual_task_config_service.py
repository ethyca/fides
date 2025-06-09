from typing import Any, Optional

from loguru import logger
from pydantic import ValidationError
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
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskAttachmentField,
    ManualTaskCheckboxField,
    ManualTaskConfigResponse,
    ManualTaskConfigurationType,
    ManualTaskField,
    ManualTaskFieldType,
    ManualTaskTextField,
)


class ManualTaskConfigService:
    def __init__(self, db: Session):
        self.db = db

    # Private Helper Methods

    def _get_fields(self, config: ManualTaskConfig) -> list[ManualTaskField]:
        """Get the fields for a config."""
        # Convert field_definitions to the format expected by ManualTaskConfigResponse
        fields = []
        for field in config.field_definitions:
            field_data = {
                "field_key": field.field_key,
                "field_type": field.field_type,
                "field_metadata": field.field_metadata,
            }
            fields.append(field_data)
        return fields

    def _get_response_data(self, config: ManualTaskConfig) -> dict[str, Any]:
        # Create response with fields
        fields = self._get_fields(config)
        return {
            "id": config.id,
            "task_id": config.task_id,
            "config_type": config.config_type,
            "version": config.version,
            "is_current": config.is_current,
            "fields": fields,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }

    def _validate_fields(self, fields: list[dict[str, Any]]) -> None:
        """Validate field data against the appropriate Pydantic model."""
        # Check for duplicate field keys
        field_keys = {}
        for field in fields:
            field_key = field.get("field_key")
            if not field_key:
                raise ValueError("Field key is required")
            if field_key in field_keys:
                raise ValueError(f"Multiple updates found for field key: {field_key}")
            field_keys[field_key] = True

        # Validate each field
        for field in fields:
            # Skip validation for fields with empty metadata (used for removal)
            if field.get("field_metadata") == {}:
                continue

            try:
                field_type = field.get("field_type")
                if field_type == ManualTaskFieldType.text:
                    ManualTaskTextField.model_validate(field)
                elif field_type == ManualTaskFieldType.checkbox:
                    ManualTaskCheckboxField.model_validate(field)
                elif field_type == ManualTaskFieldType.attachment:
                    ManualTaskAttachmentField.model_validate(field)
                else:
                    raise ValueError(f"Invalid field type: {field_type}")
            except ValidationError as e:
                raise ValueError(f"Invalid field data: {str(e)}")

    def _re_create_existing_fields(
        self,
        previous_config: ManualTaskConfig,
        new_config: ManualTaskConfig,
        modified_field_keys: set[str],
    ) -> None:
        """Re-create existing fields that aren't being modified with references to the new config."""
        # Copy only the fields that aren't being modified
        for field in previous_config.field_definitions:
            if field.field_key not in modified_field_keys:
                # Create new field record with same data
                ManualTaskConfigField.create(
                    db=self.db,
                    data={
                        "task_id": new_config.task_id,
                        "config_id": new_config.id,
                        "field_key": field.field_key,
                        "field_type": field.field_type,
                        "field_metadata": field.field_metadata,
                    },
                )

    def _new_field_updates(
        self, new_config: ManualTaskConfig, field_updates: list[dict[str, Any]]
    ) -> None:
        # Handle field updates (additions and modifications)
        if field_updates:
            for update in field_updates:
                field_key = update.get("field_key")
                if not field_key:
                    continue

                # Do not recreate if this field is empty - This is a removal
                if update["field_metadata"] == {}:
                    continue
                self._validate_fields([update])
                # Create new field with updated data - This is an add or update
                ManualTaskConfigField.create(
                    db=self.db,
                    data={
                        "task_id": new_config.task_id,
                        "config_id": new_config.id,
                        "field_key": field_key,
                        "field_type": update.get("field_type"),
                        "field_metadata": update.get("field_metadata", {}),
                    },
                )

    # Public Configuration Methods

    def to_response(
        self, config: Optional[ManualTaskConfig]
    ) -> Optional[ManualTaskConfigResponse]:
        """Convert a ManualTaskConfig model to a ManualTaskConfigResponse.

        Args:
            config: The config model to convert

        Returns:
            Optional[ManualTaskConfigResponse]: The response object, or None if config is None
        """
        if not config:
            return None
        return ManualTaskConfigResponse.model_validate(self._get_response_data(config))

    def get_current_config(
        self, task: ManualTask, config_type: str
    ) -> Optional[ManualTaskConfig]:
        """Get the current config for a task by config type."""
        config = (
            self.db.query(ManualTaskConfig)
            .filter(
                ManualTaskConfig.task_id == task.id,
                ManualTaskConfig.config_type == config_type,
                ManualTaskConfig.is_current is True,
            )
            .first()
        )

        if config:
            self.db.refresh(config)
        return config

    def list_config_type_versions(
        self, task: ManualTask, config_type: str
    ) -> list[ManualTaskConfig]:
        """List all versions of a config type for a task."""
        return (
            self.db.query(ManualTaskConfig)
            .filter(
                ManualTaskConfig.task_id == task.id,
                ManualTaskConfig.config_type == config_type,
            )
            .order_by(ManualTaskConfig.version.desc())
            .all()
        )

    def get_config(
        self,
        task: ManualTask,
        config_type: str,
        field_id: str,
        config_id: str,
        field_key: str,
        version: int,
    ) -> Optional[ManualTaskConfig]:
        """Get a task config by its id, field id, or config type."""
        if not any([task, config_id, field_id, config_type]):
            logger.warning("No filters provided to get_config. Returning None.")
            return None

        stmt = select(ManualTaskConfig)
        if task:
            stmt = stmt.where(ManualTaskConfig.task_id == task.id)
        if config_id:
            stmt = stmt.where(ManualTaskConfig.id == config_id)
        if field_id:
            stmt = stmt.where(ManualTaskConfig.field_id == field_id)
        if field_key:
            stmt = stmt.join(ManualTaskConfigField).where(
                ManualTaskConfigField.field_key == field_key
            )
        if version:
            stmt = stmt.where(ManualTaskConfig.version == version)
        if config_type:
            stmt = stmt.where(ManualTaskConfig.config_type == config_type)

        return self.db.execute(stmt).scalar_one_or_none()

    def create_new_version(
        self,
        task: ManualTask,
        config_type: str,
        field_updates: Optional[list[dict[str, Any]]] = None,
        previous_config: Optional[ManualTaskConfig] = None,
    ) -> ManualTaskConfig:
        """Create a new version of the configuration."""
        # Validate config_type
        try:
            ManualTaskConfigurationType(config_type)
        except ValueError:
            raise ValueError(f"Invalid config type: {config_type}")

        # Validate fields if provided
        if field_updates:
            self._validate_fields(field_updates)

        version = 0
        if previous_config is not None:
            version = previous_config.version
            previous_config.is_current = False

        # Track which fields are being modified or removed
        modified_field_keys = set()
        if field_updates:
            modified_field_keys = {update.get("field_key") for update in field_updates}

        # Create new version
        new_config = ManualTaskConfig.create(
            db=self.db,
            data={
                "task_id": task.id,
                "config_type": config_type,
                "version": version + 1,
                "is_current": True,
            },
        )

        # Handle field updates (fields with no changes)
        if previous_config is not None:
            self._re_create_existing_fields(
                previous_config, new_config, modified_field_keys
            )

        # Handle field updates (additions and modifications, removals)
        self._new_field_updates(new_config, field_updates)

        self.db.commit()

        # Log the version creation
        ManualTaskLog.create_log(
            db=self.db,
            task_id=task.id,
            config_id=new_config.id,
            status=ManualTaskLogStatus.created,
            message=f"Created new version {new_config.version} of configuration",
            details={
                "previous_version": (
                    previous_config.version if previous_config else None
                ),
                "field_updates": field_updates,
            },
        )

        return new_config

    def add_fields(
        self, task: ManualTask, config_type: str, fields: list[dict[str, Any]]
    ) -> None:
        """Add fields to a configuration.

        Args:
            task: The task to add fields to
            config_type: The type of config to add fields to
            fields: The fields to add
        """
        self._validate_fields(fields)
        current_config = self.get_current_config(task, config_type)
        if not current_config:
            raise ValueError(
                f"No current config found for task {task.id} and type {config_type}"
            )
        self.create_new_version(task, config_type, fields, current_config)

    def remove_fields(
        self, task: ManualTask, config_type: str, field_keys: list[str]
    ) -> None:
        """Remove fields from a configuration.

        Args:
            task: The task to remove fields from
            config_type: The type of config to remove fields from
            field_keys: The keys of the fields to remove
        """
        current_config = self.get_current_config(task, config_type)
        if not current_config:
            raise ValueError(
                f"No current config found for task {task.id} and type {config_type}"
            )

        # Get the actual ManualTaskConfig object
        config = self.db.query(ManualTaskConfig).filter_by(id=current_config.id).first()
        if not config:
            raise ValueError(f"Config with ID {current_config.id} not found")

        fields_to_remove = [
            {
                "field_key": field.field_key,
                "field_type": field.field_type,
                "field_metadata": {},
            }
            for field in config.field_definitions
            if field.field_key in field_keys
        ]
        self.create_new_version(task, config_type, fields_to_remove, config)

        # After creating the new version, remove the fields with empty metadata
        new_config = self.get_current_config(task, config_type)
        if new_config:
            for field in new_config.field_definitions:
                if field.field_key in field_keys:
                    field.delete(self.db)
            self.db.commit()

    def delete_config(self, task: ManualTask, config_id: str) -> None:
        """Delete a config for a task.

        Args:
            task: The task to delete the config for
            config_id: The ID of the config to delete

        Raises:
            ValueError: If there are active instances using this config
        """
        # TODO: when instances are implemented, we need to check for active instances

        config = (
            self.db.query(ManualTaskConfig)
            .filter(ManualTaskConfig.id == config_id)
            .first()
        )
        if not config:
            raise ValueError(f"Config with ID {config_id} not found")

        config.delete(self.db)
