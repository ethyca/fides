from typing import Any

import pytest
from sqlalchemy.exc import DataError, IntegrityError, StatementError
from sqlalchemy.orm import Session

from fides.api.models.manual_tasks.manual_task import ManualTask, ManualTaskReference
from fides.api.models.manual_tasks.manual_task_config import (
    ManualTaskConfig,
    ManualTaskConfigField,
)
from fides.api.models.manual_tasks.manual_task_log import (
    ManualTaskLog,
    ManualTaskLogStatus,
)
from fides.api.schemas.manual_tasks.manual_task_config import (
    ManualTaskConfigurationType,
    ManualTaskFieldMetadata,
    ManualTaskFieldType,
)
from fides.api.schemas.manual_tasks.manual_task_schemas import ManualTaskReferenceType

TEXT_FIELD_DATA = {
    "field_key": "test_field",
    "field_type": "text",
    "field_metadata": {
        "required": True,
        "label": "Test Field",
        "help_text": "This is a test field",
        "min_length": 1,
        "max_length": 100,
        "pattern": "^[a-zA-Z0-9]+$",
        "placeholder": "Enter a value",
        "default_value": "default_value",
    },
}

CHECKBOX_FIELD_DATA = {
    "field_key": "test_checkbox_field",
    "field_type": "checkbox",
    "field_metadata": {
        "required": True,
        "label": "Test Checkbox Field",
        "help_text": "This is a test checkbox field",
    },
}

ATTACHMENT_FIELD_DATA = {
    "field_key": "test_attachment_field",
    "field_type": "attachment",
    "field_metadata": {
        "required": True,
        "label": "Test Attachment Field",
        "help_text": "This is a test attachment field",
    },
}


class TestManualTaskConfig:
    def test_create_config(self, db: Session, manual_task: ManualTask):
        config = ManualTaskConfig.create(
            db,
            data={
                "task_id": manual_task.id,
                "config_type": "access_privacy_request",
                "version": 1,
                "is_current": True,
            },
        )
        assert config.id is not None
        assert config.task_id == manual_task.id
        assert config.config_type == "access_privacy_request"
        assert config.version == 1
        assert config.is_current == True
        assert config.field_definitions == []

    @pytest.mark.parametrize(
        "invalid_types, expected_error",
        [
            pytest.param(
                {"config_type": "invalid_config_type"},
                ValueError,
                id="invalid_config_type",
            ),
            pytest.param({"version": "not_an_int"}, DataError, id="invalid_version"),
            pytest.param(
                {"is_current": "not_a_bool"}, StatementError, id="invalid_is_current"
            ),
            pytest.param(
                {"task_id": "not_a_string"}, IntegrityError, id="invalid_task_id"
            ),
            pytest.param({"invalid_key": "invalid_value"}, TypeError, id="invalid_key"),
        ],
    )
    def test_create_config_error(
        self,
        db: Session,
        manual_task: ManualTask,
        invalid_types: dict[str, Any],
        expected_error: type[Exception],
    ):
        data = {
            "task_id": manual_task.id,
            "config_type": "access_privacy_request",
            "version": 1,
            "is_current": True,
        }
        data.update(invalid_types)
        with pytest.raises(expected_error) as exc_info:
            ManualTaskConfig.create(db, data=data)
        assert list(invalid_types.keys())[0] in str(exc_info.value)

    def test_relationships(self, db: Session, manual_task: ManualTask):
        config = ManualTaskConfig.create(
            db,
            data={
                "task_id": manual_task.id,
                "config_type": "access_privacy_request",
                "version": 1,
                "is_current": True,
            },
        )
        assert config.task == manual_task
        assert config.field_definitions == []
        assert len(config.logs) == 1
        assert config.logs[0].config_id == config.id
        assert config.logs[0].task_id == manual_task.id
        assert config.logs[0].status == ManualTaskLogStatus.created

        data = TEXT_FIELD_DATA.copy()
        data["task_id"] = manual_task.id
        data["config_id"] = config.id
        ManualTaskConfigField.create(db, data=data)

        assert len(config.field_definitions) == 1


@pytest.mark.parametrize(
    "field_data, expected_field_type",
    [
        pytest.param(TEXT_FIELD_DATA, ManualTaskFieldType.text, id="text_field"),
        pytest.param(
            CHECKBOX_FIELD_DATA, ManualTaskFieldType.checkbox, id="checkbox_field"
        ),
        pytest.param(
            ATTACHMENT_FIELD_DATA, ManualTaskFieldType.attachment, id="attachment_field"
        ),
    ],
)
class TestManualTaskConfigField:

    def test_create_field(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        field_data: dict[str, Any],
        expected_field_type: ManualTaskFieldType,
    ):
        data = field_data.copy()
        data["task_id"] = manual_task.id
        data["config_id"] = manual_task_config.id
        field = ManualTaskConfigField.create(db, data=data)
        assert field.id is not None
        assert field.task_id == manual_task.id
        assert field.config_id == manual_task_config.id
        assert field.field_key == field_data["field_key"]
        assert field.field_type == expected_field_type
        assert field.field_metadata == field_data["field_metadata"]

        assert field.field_metadata_model == ManualTaskFieldMetadata.model_validate(
            field_data["field_metadata"]
        )

        assert field.config == manual_task_config
        assert len(manual_task_config.field_definitions) == 1
        assert manual_task_config.field_definitions[0] == field
        assert manual_task_config.get_field(field.field_key) == field

    @pytest.mark.parametrize(
        "invalid_types, expected_error",
        [
            pytest.param({"field_key": None}, IntegrityError, id="invalid_field_key"),
            pytest.param(
                {"field_type": "invalid_field_type"},
                IntegrityError,
                id="invalid_field_type",
            ),
            pytest.param({"task_id": 9}, IntegrityError, id="invalid_task_id"),
            pytest.param({"config_id": 9}, IntegrityError, id="invalid_config_id"),
            pytest.param({"invalid_key": "invalid_value"}, TypeError, id="invalid_key"),
        ],
    )
    def test_create_field_error(
        self,
        db: Session,
        manual_task: ManualTask,
        manual_task_config: ManualTaskConfig,
        field_data: dict[str, Any],
        expected_field_type: ManualTaskFieldType,
        invalid_types: dict[str, Any],
        expected_error: type[Exception],
    ):
        data = field_data.copy()
        data["task_id"] = manual_task.id
        data["config_id"] = manual_task_config.id

        data.update(invalid_types)
        with pytest.raises(expected_error) as exc_info:
            ManualTaskConfigField.create(db, data=data)
        assert list(invalid_types.keys())[0] in str(exc_info.value)
