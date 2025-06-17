from typing import Any

import pytest
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import ManualTask
from fides.api.models.manual_tasks.manual_task_config import ManualTaskConfig
from fides.api.models.manual_tasks.manual_task_log import (
    ManualTaskLog,
    ManualTaskLogStatus,
)
from fides.api.schemas.manual_tasks.manual_task_config import ManualTaskFieldType
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskLogStatus
from fides.service.manual_tasks.manual_task_config_service import (
    ManualTaskConfigService,
)
from tests.service.manual_tasks.conftest import (
    ATTACHMENT_FIELD_KEY,
    CHECKBOX_FIELD_KEY,
    CONFIG_TYPE,
    FIELDS,
    TEXT_FIELD_KEY,
)


@pytest.fixture
def manual_task(db: Session):
    task = ManualTask.create(
        db=db,
        data={
            "parent_entity_id": "test-parent-id",
            "parent_entity_type": "connection_config",
            "task_type": "privacy_request",
        },
    )
    yield task
    task.delete(db)


@pytest.fixture
def manual_task_config_service(db: Session):
    return ManualTaskConfigService(db)


def test_create_new_version_no_previous_config(
    db: Session,
    manual_task: ManualTask,
    manual_task_config_service: ManualTaskConfigService,
):
    """Test creating a new version when there is no previous config."""
    config = manual_task_config_service.create_new_version(
        task=manual_task,
        config_type=CONFIG_TYPE,
        field_updates=FIELDS,
    )

    assert config.config_type == CONFIG_TYPE
    assert config.version == 1
    assert config.is_current is True
    assert len(config.field_definitions) == len(FIELDS)

    # Verify field definitions match input
    for field_def, field_input in zip(
        sorted(config.field_definitions, key=lambda x: x.field_key),
        sorted(FIELDS, key=lambda x: x["field_key"]),
    ):
        assert field_def.field_key == field_input["field_key"]
        assert field_def.field_type == field_input["field_type"]
        assert (
            field_def.field_metadata["label"] == field_input["field_metadata"]["label"]
        )

    # Verify log was created
    log = (
        db.query(ManualTaskLog)
        .filter_by(task_id=manual_task.id)
        .order_by(ManualTaskLog.created_at.desc())
        .first()
    )
    assert log.status == ManualTaskLogStatus.complete
    assert "Creating new configuration version" in log.message
    assert log.config_id == config.id


def test_create_new_version_with_previous_config(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    manual_task_config_service: ManualTaskConfigService,
):
    """Test creating a new version when there is a previous config."""
    modified_fields = [
        {
            "field_key": TEXT_FIELD_KEY,
            "field_type": ManualTaskFieldType.text,
            "field_metadata": {
                "label": "Text Field Updated",
                "required": True,
                "help_text": "This is text field updated",
            },
        }
    ]
    new_config = manual_task_config_service.create_new_version(
        task=manual_task,
        config_type=CONFIG_TYPE,
        field_updates=modified_fields,
        previous_config=manual_task_config,
    )

    assert new_config.config_type == CONFIG_TYPE
    assert new_config.version == 2
    assert new_config.is_current is True
    assert not manual_task_config.is_current

    # Verify updated field
    text_field = next(
        field
        for field in new_config.field_definitions
        if field.field_key == TEXT_FIELD_KEY
    )
    assert text_field.field_metadata["label"] == "Text Field Updated"

    # Verify other fields remained unchanged
    checkbox_field = next(
        field
        for field in new_config.field_definitions
        if field.field_key == CHECKBOX_FIELD_KEY
    )
    assert checkbox_field.field_metadata["label"] == "Test Checkbox Field"


@pytest.mark.parametrize(
    "invalid_input,expected_error",
    [
        (
            {"config_type": "invalid_type", "fields": FIELDS},
            "Invalid config type: invalid_type",
        ),
        (
            {
                "config_type": CONFIG_TYPE,
                "fields": [
                    {
                        "field_key": TEXT_FIELD_KEY,
                        "field_type": "invalid_type",
                        "field_metadata": {"label": "Text Field", "required": True},
                    }
                ],
            },
            "Invalid field type: 'invalid_type' is not a valid ManualTaskFieldType",
        ),
        (
            {
                "config_type": CONFIG_TYPE,
                "fields": [
                    {
                        "field_key": TEXT_FIELD_KEY,
                        "field_type": None,
                        "field_metadata": {"label": "Field 1", "required": True},
                    }
                ],
            },
            "Invalid field data: field_type is required",
        ),
        (
            {
                "config_type": CONFIG_TYPE,
                "fields": [
                    {
                        "field_key": "",
                        "field_type": ManualTaskFieldType.text,
                        "field_metadata": {"label": "Field 1", "required": True},
                    }
                ],
            },
            "Invalid field data",
        ),
        (
            {
                "config_type": CONFIG_TYPE,
                "fields": [
                    {
                        "field_key": TEXT_FIELD_KEY,
                        "field_type": ManualTaskFieldType.text,
                        "field_metadata": {"invalid_key": "value"},
                    }
                ],
            },
            "Invalid field data",
        ),
    ],
)
def test_config_validation(
    manual_task: ManualTask,
    manual_task_config_service: ManualTaskConfigService,
    invalid_input: dict[str, Any],
    expected_error: str,
):
    """Test various config validation scenarios."""
    with pytest.raises(ValueError, match=expected_error):
        manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=invalid_input["config_type"],
            field_updates=invalid_input["fields"],
        )


def test_duplicate_field_keys(
    manual_task: ManualTask,
    manual_task_config_service: ManualTaskConfigService,
):
    """Test that multiple updates to the same field are rejected."""
    duplicate_fields = [
        {
            "field_key": TEXT_FIELD_KEY,
            "field_type": ManualTaskFieldType.text,
            "field_metadata": {"label": "Field 1", "required": True},
        },
        {
            "field_key": TEXT_FIELD_KEY,
            "field_type": ManualTaskFieldType.text,
            "field_metadata": {"label": "Field 1 Duplicate", "required": False},
        },
    ]
    with pytest.raises(
        ValueError,
        match="Duplicate field keys found in field updates, field keys must be unique.",
    ):
        manual_task_config_service.create_new_version(
            task=manual_task,
            config_type=CONFIG_TYPE,
            field_updates=duplicate_fields,
        )


def test_config_retrieval(
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    manual_task_config_service: ManualTaskConfigService,
):
    """Test various config retrieval methods."""
    # Get by ID
    config = manual_task_config_service.get_config(
        task=manual_task,
        config_type=CONFIG_TYPE,
        field_id=None,
        config_id=manual_task_config.id,
        field_key=None,
        version=None,
    )
    assert config.id == manual_task_config.id

    # Get by version
    config = manual_task_config_service.get_config(
        task=manual_task,
        config_type=CONFIG_TYPE,
        field_id=None,
        config_id=None,
        field_key=None,
        version=1,
    )
    assert config.version == 1

    # Get by field key
    config = manual_task_config_service.get_config(
        task=manual_task,
        config_type=CONFIG_TYPE,
        field_id=None,
        config_id=None,
        field_key=TEXT_FIELD_KEY,
        version=None,
    )
    assert any(field.field_key == TEXT_FIELD_KEY for field in config.field_definitions)

    # Get with no filters
    assert (
        manual_task_config_service.get_config(
            task=None,
            config_type=None,
            field_id=None,
            config_id=None,
            field_key=None,
            version=None,
        )
        is None
    )


def test_field_management(
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    manual_task_config_service: ManualTaskConfigService,
):
    """Test field addition and removal."""
    # Add new field
    new_field = {
        "field_key": "new_field",
        "field_type": ManualTaskFieldType.text,
        "field_metadata": {
            "label": "New Field",
            "required": False,
            "help_text": "This is a new field",
        },
    }
    manual_task_config_service.add_fields(manual_task, CONFIG_TYPE, [new_field])
    current_config = manual_task_config_service.get_current_config(
        manual_task, CONFIG_TYPE
    )
    assert len(current_config.field_definitions) == len(FIELDS) + 1
    assert any(
        field.field_key == "new_field" for field in current_config.field_definitions
    )

    # Remove field
    manual_task_config_service.remove_fields(manual_task, CONFIG_TYPE, [TEXT_FIELD_KEY])
    current_config = manual_task_config_service.get_current_config(
        manual_task, CONFIG_TYPE
    )
    assert len(current_config.field_definitions) == len(FIELDS)
    assert not any(
        field.field_key == TEXT_FIELD_KEY for field in current_config.field_definitions
    )


def test_config_deletion(
    db: Session,
    manual_task: ManualTask,
    manual_task_config: ManualTaskConfig,
    manual_task_config_service: ManualTaskConfigService,
):
    """Test config deletion."""
    config_id = manual_task_config.id
    manual_task_config_service.delete_config(manual_task, config_id)
    assert db.query(ManualTaskConfig).filter_by(id=config_id).first() is None

    with pytest.raises(ValueError, match="Config with ID invalid-id not found"):
        manual_task_config_service.delete_config(manual_task, "invalid-id")


def test_config_response_conversion(
    manual_task_config: ManualTaskConfig,
    manual_task_config_service: ManualTaskConfigService,
):
    """Test converting config to response object."""
    response = manual_task_config_service.to_response(manual_task_config)
    assert response.id == manual_task_config.id
    assert response.task_id == manual_task_config.task_id
    assert response.config_type == manual_task_config.config_type
    assert response.version == manual_task_config.version
    assert response.is_current == manual_task_config.is_current
    assert len(response.fields) == len(FIELDS)

    for field, expected_field in zip(
        sorted(response.fields, key=lambda x: x.field_key),
        sorted(FIELDS, key=lambda x: x["field_key"]),
    ):
        assert field.field_key == expected_field["field_key"]
        assert field.field_type == expected_field["field_type"]
        assert field.field_metadata.label == expected_field["field_metadata"]["label"]
        assert (
            field.field_metadata.required
            == expected_field["field_metadata"]["required"]
        )
