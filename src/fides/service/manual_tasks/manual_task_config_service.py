from typing import Any, Optional

from loguru import logger
from sqlalchemy.orm import Query, Session, selectinload

from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
)
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskConfigResponse,
    ManualTaskConfigurationType,
)
from fides.service.manual_tasks.utils import validate_fields, with_task_logging


class ManualTaskConfigService:
    def __init__(self, db: Session):
        self.db = db

    def _create_log_data(
        self, task_id: str, config_id: Optional[str], details: dict[str, Any]
    ) -> dict[str, Any]:
        """Create standard log data structure."""
        return {"task_id": task_id, "config_id": config_id, "details": details}

    def _get_base_config_query(self) -> Query:
        """Get base config query with field definitions loaded."""
        return self.db.query(ManualTaskConfig).options(
            selectinload(ManualTaskConfig.field_definitions)
        )

    def _create_config_version(
        self,
        task: ManualTask,
        config_type: str,
        version: int,
        is_current: bool = True,
    ) -> ManualTaskConfig:
        """Create a new config version. This is a helper method that creates a new config
        version and sets it as the current version.

        Args:
            task: The task to create the config for
            config_type: The type of config to create
            version: The version number of the config
            is_current: Whether the config is the current version
        Returns:
            The new config
        """
        try:
            ManualTaskConfigurationType(config_type)
        except ValueError:
            raise ValueError(f"Invalid config type: {config_type}")

        # Set all existing versions to non-current
        if is_current:
            self.db.query(ManualTaskConfig).filter(
                ManualTaskConfig.task_id == task.id,
                ManualTaskConfig.config_type == config_type,
            ).update({"is_current": False})
            self.db.flush()

        return ManualTaskConfig.create(
            db=self.db,
            data={
                "task_id": task.id,
                "config_type": config_type,
                "version": version,
                "is_current": is_current,
            },
        )

    def _handle_field_updates(
        self,
        config: ManualTaskConfig,
        field_updates: Optional[list[dict[str, Any]]] = None,
        fields_to_remove: Optional[list[str]] = None,
        previous_config: Optional[ManualTaskConfig] = None,
    ) -> set[str]:
        """Handle field updates, removals, and recreation from previous version. This is a helper
        function that:
        - Creates new fields from field_updates
        - Recreates unmodified fields from previous version so they will remain in the config
        - Removes fields that are no longer in the config

        Args:
            config: The config to update
            field_updates: The fields to update
            fields_to_remove: The fields to remove
            previous_config: The previous config
        Returns:
            The modified keys
        """
        modified_keys = set(fields_to_remove or [])

        if field_updates:
            validate_fields(field_updates, is_submission=False)
            fields_to_create = [
                {
                    "task_id": config.task_id,
                    "config_id": config.id,
                    "field_key": f["field_key"],
                    "field_type": f.get("field_type"),
                    "field_metadata": f.get("field_metadata", {}),
                }
                for f in field_updates
            ]
            if fields_to_create:
                self.db.bulk_insert_mappings(ManualTaskConfigField, fields_to_create)
                modified_keys.update(f["field_key"] for f in field_updates)

        if previous_config:
            # Recreate unmodified fields from previous version
            unmodified = [
                {
                    "task_id": config.task_id,
                    "config_id": config.id,
                    "field_key": f.field_key,
                    "field_type": f.field_type,
                    "field_metadata": f.field_metadata,
                }
                for f in previous_config.field_definitions
                if f.field_key not in modified_keys
            ]
            if unmodified:
                self.db.bulk_insert_mappings(ManualTaskConfigField, unmodified)

        self.db.flush()
        return modified_keys

    def to_response(self, config: ManualTaskConfig) -> ManualTaskConfigResponse:
        """Convert config model to response object."""
        return ManualTaskConfigResponse.model_validate(
            {
                "id": config.id,
                "task_id": config.task_id,
                "config_type": config.config_type,
                "version": config.version,
                "is_current": config.is_current,
                "fields": [
                    {
                        "field_key": f.field_key,
                        "field_type": f.field_type,
                        "field_metadata": f.field_metadata,
                    }
                    for f in config.field_definitions
                ],
                "created_at": config.created_at,
                "updated_at": config.updated_at,
            }
        )

    def get_current_config(
        self, task: ManualTask, config_type: str
    ) -> ManualTaskConfig:
        """Get current config for task by type."""
        config = (
            self._get_base_config_query()
            .filter(
                ManualTaskConfig.task_id == task.id,
                ManualTaskConfig.config_type == config_type,
                ManualTaskConfig.is_current.is_(True),
            )
            .first()
        )

        if not config:
            raise ValueError(
                f"No current config found for task {task.id} and type {config_type}"
            )
        return config

    def list_config_type_versions(
        self, task: ManualTask, config_type: str
    ) -> list[ManualTaskConfig]:
        """List all versions of a config type for a task."""
        return (
            self._get_base_config_query()
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
        """Get config by various filters. This is a flexible lookup method that can find configs based on various filters.

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
            logger.debug("No filters provided to get_config")
            return None

        query = self._get_base_config_query()
        if field_id or field_key:
            query = query.join(ManualTaskConfig.field_definitions)

        filters = [
            f
            for f in [
                task and ManualTaskConfig.task_id == task.id,
                config_id and ManualTaskConfig.id == config_id,
                field_id and ManualTaskConfigField.id == field_id,
                field_key and ManualTaskConfigField.field_key == field_key,
                version and ManualTaskConfig.version == version,
                config_type and ManualTaskConfig.config_type == config_type,
            ]
            if f
        ]

        return query.filter(*filters).first()

    @with_task_logging("Creating new configuration version")
    def create_new_version(
        self,
        task: ManualTask,
        config_type: str,
        field_updates: Optional[list[dict[str, Any]]] = None,
        fields_to_remove: Optional[list[str]] = None,
        previous_config: Optional[ManualTaskConfig] = None,
    ) -> tuple[ManualTaskConfig, dict[str, Any]]:
        """Create new version of configuration.

        Args:
            task: The task to create the config for
            config_type: The type of config to create
            field_updates: The fields to update
            fields_to_remove: The fields to remove
            previous_config: The previous config

        Returns:
            Tuple containing the new config and log data, the log data is
            captured by the with_task_logging decorator. and the new config is
            returned to the caller.
        """
        new_config = self._create_config_version(
            task, config_type, (previous_config.version + 1 if previous_config else 1)
        )

        self._handle_field_updates(
            new_config, field_updates, fields_to_remove, previous_config
        )

        return new_config, self._create_log_data(
            task.id,
            new_config.id,
            {
                "config_type": config_type,
                "version": new_config.version,
                "added_field_keys": [f.get("field_key") for f in (field_updates or [])],
                "removed_field_keys": fields_to_remove or [],
            },
        )

    @with_task_logging("Adding fields to configuration")
    def add_fields(
        self, task: ManualTask, config_type: str, fields: list[dict[str, Any]]
    ) -> tuple[ManualTaskConfig, dict[str, Any]]:
        """Add fields to configuration.

        Args:
            task: The task to add the fields to
            config_type: The type of config to add the fields to
            fields: The fields to add

        Returns:
            Tuple containing the new config and log data, the log data is
            captured by the with_task_logging decorator. and the new config is
            returned to the caller.
        """
        current = self.get_current_config(task, config_type)
        self.create_new_version(task, config_type, fields, previous_config=current)
        new_config = self.get_current_config(task, config_type)

        return new_config, self._create_log_data(
            task.id,
            current.id,
            {
                "config_type": config_type,
                "previous_version": current.version,
                "added_field_keys": [f.get("field_key") for f in fields],
                "new_config_id": new_config.id,
                "new_config_version": new_config.version,
            },
        )

    @with_task_logging("Removing fields from configuration")
    def remove_fields(
        self, task: ManualTask, config_type: str, field_keys: list[str]
    ) -> tuple[ManualTaskConfig, dict[str, Any]]:
        """Remove fields from configuration.

        Args:
            task: The task to remove the fields from
            config_type: The type of config to remove the fields from
            field_keys: The keys of the fields to remove

        Returns:
            Tuple containing the new config and log data, the log data is
            captured by the with_task_logging decorator. and the new config is
            returned to the caller.
        """
        current = self.get_current_config(task, config_type)
        self.create_new_version(
            task, config_type, fields_to_remove=field_keys, previous_config=current
        )
        new_config = self.get_current_config(task, config_type)

        return new_config, self._create_log_data(
            task.id,
            current.id,
            {
                "config_type": config_type,
                "version": current.version,
                "deleted_field_keys": field_keys,
                "new_config_id": new_config.id,
                "new_config_version": new_config.version,
            },
        )

    @with_task_logging("Deleting Manual Task configuration")
    def delete_config(
        self, task: ManualTask, config_id: str
    ) -> tuple[ManualTaskConfig, dict[str, Any]]:
        """Delete config for task.

        Args:
            task: The task to delete the config for
            config_id: The ID of the config to delete

        Returns:
            Tuple containing the deleted config and log data, the log data is
            captured by the with_task_logging decorator. and the deleted config is
            returned to the caller.
        """
        config = self.db.query(ManualTaskConfig).filter_by(id=config_id).first()
        if not config:
            raise ValueError(f"Config with ID {config_id} not found")

        log_data = self._create_log_data(
            task.id,
            None,
            {
                "config_type": config.config_type,
                "version": config.version,
                "deleted_config_id": config_id,
            },
        )
        config.delete(self.db)
        return config, log_data
