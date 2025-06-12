from typing import Any, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
)
from fides.api.models.manual_tasks.manual_task_instance import ManualTaskInstance
from fides.api.models.manual_tasks.manual_task_log import ManualTaskLog
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskConfigResponse,
    ManualTaskConfigurationType,
    ManualTaskFieldBase,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskLogStatus
from fides.api.schemas.manual_tasks.manual_task_status import StatusType
from fides.service.manual_tasks.utils import validate_fields


class ManualTaskConfigService:
    def __init__(self, db: Session):
        self.db = db

    # ------- Private Helper Methods -------

    def _get_fields(self, config: ManualTaskConfig) -> list[dict[str, Any]]:
        """Get the fields for a config and returns them in the format expected by ManualTaskConfigResponse"""
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
        """Get the data for a config and returns it in the format expected by ManualTaskConfigResponse"""
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
        """Validate field data against the appropriate Pydantic model.
        Raises a ValueError if the field data is invalid.
        """
        # Check for duplicate field keys
        field_keys_set: set[str] = {str(field.get("field_key")) for field in fields}
        if len(field_keys_set) != len(fields):
            raise ValueError(
                "Duplicate field keys found in field updates, field keys must be unique."
            )
        # Check that field_key is present for each field
        for field in fields:
            field_key = field.get("field_key")
            if not field_key:
                raise ValueError("Invalid field data: field_key is required")
            # Skip validation for fields with empty metadata (used for removal)
            if field.get("field_metadata") == {}:
                continue

            try:
                field_type = field.get("field_type")
                if not field_type:
                    raise ValueError("Invalid field data: field_type is required")

                field_model = ManualTaskFieldBase.get_field_model_for_type(field_type)
                field_model.model_validate(field)
            except ValidationError as e:
                raise ValueError(f"Invalid field data: {str(e)}")
            except ValueError as e:
                raise ValueError(str(e))

    def _re_create_existing_fields(
        self,
        previous_config: ManualTaskConfig,
        new_config: ManualTaskConfig,
        modified_field_keys: set[str],
    ) -> None:
        """Re-create fields from the previous config version that aren't being modified in the new version.

        When creating a new config version, we need to carry over any fields that aren't being
        modified or removed. This method handles that by:
        1. Looking at all fields in the previous config
        2. For each field not in modified_field_keys (not being updated or removed):
           - Creates a new field record with the same data but linked to the new config

        This ensures that fields maintain continuity across versions unless explicitly changed.

        Args:
            previous_config: The previous version of the configuration
            new_config: The new version being created
            modified_field_keys: Set of field keys that are being updated or removed in the new version
        """
        # Prepare bulk insert data for unmodified fields
        fields_to_create = [
            {
                "task_id": new_config.task_id,
                "config_id": new_config.id,
                "field_key": field.field_key,
                "field_type": field.field_type,
                "field_metadata": field.field_metadata,
            }
            for field in previous_config.field_definitions
            if field.field_key not in modified_field_keys
        ]

        # Perform bulk insert if there are fields to create
        if fields_to_create:
            self.db.bulk_insert_mappings(ManualTaskConfigField, fields_to_create)
            self.db.flush()

    def _new_field_updates(
        self, new_config: ManualTaskConfig, field_updates: list[dict[str, Any]]
    ) -> None:
        """Updates fields for a config.
        Args:
            new_config: The config to add fields to
            field_updates: The fields to add or update
        """
        validate_fields(field_updates)

        # Prepare bulk insert data
        fields_to_create = [
            {
                "task_id": new_config.task_id,
                "config_id": new_config.id,
                "field_key": update["field_key"],
                "field_type": update.get("field_type"),
                "field_metadata": update.get("field_metadata", {}),
            }
            for update in field_updates
        ]

        # Perform bulk insert
        if fields_to_create:
            self.db.bulk_insert_mappings(ManualTaskConfigField, fields_to_create)
            self.db.flush()

    # ------- Public Configuration Methods -------

    def to_response(self, config: ManualTaskConfig) -> ManualTaskConfigResponse:
        """Convert a ManualTaskConfig model to a ManualTaskConfigResponse.

        Args:
            config: The config model to convert

        Returns:
            Optional[ManualTaskConfigResponse]: The response object, or None if config is None
        """
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
                ManualTaskConfig.is_current.is_(True),
            )
            .first()
        )

        if config:
            self.db.refresh(config)
            return config
        raise ValueError(
            f"No current config found for task {task.id} and type {config_type}"
        )

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
        """Get a task config by its id, field id, or config type.

        This is a flexible lookup method that can find configs based on various filters.
        It's normal for this method to return None if no config matches the given filters.

        Args:
            task: The task to get the config for
            config_type: The type of config to get
            field_id: The ID of a field in the config
            config_id: The ID of the config
            field_key: The key of a field in the config
            version: The version number of the config

        Returns:
            The matching config if found, None otherwise
        """
        if not any([task, config_id, field_id, config_type]):
            logger.debug("No filters provided to get_config. Returning None.")
            return None

        # Start with base query and add joins only if needed
        query = self.db.query(ManualTaskConfig)

        # Add join only once if either field_id or field_key is provided
        if field_id or field_key:
            query = query.join(ManualTaskConfigField)

        # Build filter conditions
        filters = []
        if task:
            filters.append(ManualTaskConfig.task_id == task.id)
        if config_id:
            filters.append(ManualTaskConfig.id == config_id)
        if field_id:
            filters.append(ManualTaskConfigField.id == field_id)
        if field_key:
            filters.append(ManualTaskConfigField.field_key == field_key)
        if version:
            filters.append(ManualTaskConfig.version == version)
        if config_type:
            filters.append(ManualTaskConfig.config_type == config_type)

        # Apply all filters at once
        if filters:
            query = query.filter(*filters)

        result = query.first()
        if not result:
            logger.debug(
                "No config found that matches filters: "
                f"task {task.id if task else None}, "
                f"config_id {config_id}, "
                f"field_id {field_id}, "
                f"field_key {field_key}, "
                f"version {version}, "
                f"config_type {config_type}"
            )
            return None

        self.db.refresh(result)
        return result

    def create_new_version(
        self,
        task: ManualTask,
        config_type: str,
        field_updates: Optional[list[dict[str, Any]]] = None,
        fields_to_remove: Optional[list[str]] = None,
        previous_config: Optional[ManualTaskConfig] = None,
    ) -> ManualTaskConfig:
        """Create a new version of the configuration.

        Args:
            task: The task to create a config for
            config_type: The type of config to create
            field_updates: Fields to add or update
            fields_to_remove: Field keys to remove
            previous_config: The previous config version, if any
        """
        new_version = previous_config.version + 1 if previous_config else 1
        # Validate config_type
        try:
            ManualTaskConfigurationType(config_type)
        except ValueError:
            raise ValueError(f"Invalid config type: {config_type}")

        # Create new version
        new_config = ManualTaskConfig.create(
            db=self.db,
            data={
                "task_id": task.id,
                "config_type": config_type,
                "version": new_version,
                "is_current": True,
            },
        )
        modified_field_keys: set[str] = set()

        # Handle field updates (additions and modifications)
        if field_updates:
            validate_fields(field_updates)
            self._new_field_updates(new_config, field_updates)
            modified_field_keys.update(
                str(update.get("field_key")) for update in field_updates
            )

        # Handle field removals
        if fields_to_remove:
            modified_field_keys.update(fields_to_remove)

        # Handle field updates (fields with no changes)
        if previous_config is not None:
            previous_config.is_current = False
            self._re_create_existing_fields(
                previous_config,
                new_config,
                modified_field_keys,
            )

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
                "fields_removed": fields_to_remove,
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
        validate_fields(fields)
        current_config = self.get_current_config(task, config_type)
        if not current_config:
            raise ValueError(
                f"No current config found for task {task.id} and type {config_type}"
            )

        self.create_new_version(
            task=task,
            config_type=config_type,
            field_updates=fields,
            previous_config=current_config,
        )

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

        # Get the actual ManualTaskConfig object with field definitions
        config = self.db.query(ManualTaskConfig).filter_by(id=current_config.id).first()
        if not config:
            raise ValueError(f"Config with ID {current_config.id} not found")

        # Create new version with removed fields
        self.create_new_version(
            task=task,
            config_type=config_type,
            fields_to_remove=field_keys,
            previous_config=config,
        )

    def get_active_instances(self, config_id: str) -> list[ManualTaskInstance]:
        """Get all active instances for a config."""
        return (
            self.db.query(ManualTaskInstance)
            .filter(
                ManualTaskInstance.config_id == config_id,
                ManualTaskInstance.status != StatusType.completed,
            )
            .all()
        )

    def delete_config(self, task: ManualTask, config_id: str) -> None:
        """Delete a config for a task.

        Args:
            task: The task to delete the config for
            config_id: The ID of the config to delete

        Raises:
            ValueError: If there are active instances using this config
        """
        config = (
            self.db.query(ManualTaskConfig)
            .filter(ManualTaskConfig.id == config_id)
            .first()
        )
        if not config:
            raise ValueError(f"Config with ID {config_id} not found")
        if self.get_active_instances(config_id):
            raise ValueError("Cannot delete config with active instances")

        config.delete(self.db)
