import pytest
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskInstance,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import (
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskType,
)


@pytest.fixture
def form_field_data():
    """Fixture for form field data."""
    return {
        "label": "Test Form Field",
        "required": True,
        "help_text": "This is a test form field",
    }


@pytest.fixture
def checkbox_field_data():
    """Fixture for checkbox field data."""
    return {
        "label": "Test Checkbox Field",
        "required": True,
        "help_text": "This is a test checkbox field",
        "default_value": False,
    }


@pytest.fixture
def attachment_field_data():
    """Fixture for attachment field data."""
    return {
        "label": "Test Attachment Field",
        "required": True,
        "help_text": "This is a test attachment field",
        "file_types": ["pdf"],
        "max_file_size": 1048576,
        "multiple": True,
        "max_files": 2,
        "require_attachment_id": True,
    }


@pytest.fixture
def manual_task(db: Session) -> ManualTask:
    """Create a test manual task."""
    task = ManualTask.create(
        db=db,
        data={
            "task_type": ManualTaskType.privacy_request,
            "parent_entity_id": "test_connection",
            "parent_entity_type": "connection_config",
        },
    )
    return task


@pytest.fixture
def manual_task_config(db: Session, manual_task: ManualTask) -> ManualTaskConfig:
    """Create a test manual task configuration."""
    config = ManualTaskConfig.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_type": ManualTaskConfigurationType.access_privacy_request,
        },
    )
    return config


@pytest.fixture
def manual_task_form_field(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    form_field_data: dict,
) -> ManualTaskConfigField:
    """Create a test form field."""
    field = ManualTaskConfigField.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_task_config.id,
            "field_key": "test_form_field",
            "field_type": ManualTaskFieldType.form,
            "field_metadata": form_field_data,
        },
    )
    manual_task_config.field_definitions.append(field)
    db.commit()
    return field


@pytest.fixture
def manual_task_checkbox_field(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    checkbox_field_data: dict,
) -> ManualTaskConfigField:
    """Create a test checkbox field."""
    field = ManualTaskConfigField.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_task_config.id,
            "field_key": "test_checkbox_field",
            "field_type": ManualTaskFieldType.checkbox,
            "field_metadata": checkbox_field_data,
        },
    )
    manual_task_config.field_definitions.append(field)
    db.commit()
    return field


@pytest.fixture
def manual_task_attachment_field(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    attachment_field_data: dict,
) -> ManualTaskConfigField:
    """Create a test attachment field."""
    field = ManualTaskConfigField.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_task_config.id,
            "field_key": "test_attachment_field",
            "field_type": ManualTaskFieldType.attachment,
            "field_metadata": attachment_field_data,
        },
    )
    manual_task_config.field_definitions.append(field)
    db.commit()
    return field


@pytest.fixture
def manual_task_config_with_fields(
    db: Session,
    manual_task: ManualTask,
    manual_task_form_field: ManualTaskConfigField,
    manual_task_checkbox_field: ManualTaskConfigField,
    manual_task_attachment_field: ManualTaskConfigField,
) -> ManualTaskConfig:
    """Create a test config with all field types."""
    return manual_task_form_field.config


@pytest.fixture
def manual_task_field(
    db: Session, manual_task_config: ManualTaskConfig
) -> ManualTaskConfigField:
    """Create a test manual task field."""
    field = ManualTaskConfigField.create(
        db=db,
        data={
            "task_id": manual_task_config.task_id,
            "config_id": manual_task_config.id,
            "field_key": "test_field",
            "field_type": ManualTaskFieldType.form,
            "field_metadata": {
                "label": "Test Field",
                "required": True,
                "help_text": "This is a test field",
            },
        },
    )
    # Ensure the field is added to the config's field_definitions
    manual_task_config.field_definitions.append(field)
    db.commit()
    return field


@pytest.fixture
def manual_task_instance(
    db: Session, manual_task: ManualTask, manual_task_config: ManualTaskConfig
) -> ManualTaskInstance:
    """Create a test manual task instance."""
    instance = manual_task.create_entity_instance(
        db=db,
        config_id=manual_task_config.id,
        entity_id="test_privacy_request",
        entity_type="privacy_request",
    )
    return instance
