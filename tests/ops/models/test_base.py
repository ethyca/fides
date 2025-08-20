from __future__ import annotations

from typing import Any

import pytest
from fideslang.validation import FidesValidationError
from sqlalchemy.orm import Session

from fides.api.common_exceptions import KeyValidationError
from fides.api.db.base_class import FidesBase, get_key_from_data
from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import StorageType


def test_get_key_from_data_method_invalid_key() -> None:
    # Test key not valid
    with pytest.raises(FidesValidationError) as exc:
        get_key_from_data({"key": "test*key", "name": "config name"}, "StorageConfig")
    assert (
        str(exc.value)
        == "FidesKeys must only contain alphanumeric characters, '.', '_', '<', '>' or '-'. Value provided: test*key"
    )


def test_create_key(db: Session):
    # Test no way to create a key
    with pytest.raises(KeyValidationError) as exc:
        StorageConfig.create(
            db,
            data={
                "type": StorageType.s3.value,
                "details": {
                    "bucket": "some-bucket",
                },
            },
        )
    assert str(exc.value) == "StorageConfig requires a name."

    # Test happy path
    sc = StorageConfig.create(
        db,
        data={
            "name": "test dest",
            "type": StorageType.s3.value,
            "details": {
                "bucket": "some-bucket",
                "naming": "some-filename-convention-enum",
                "max_retries": 10,
            },
        },
    )

    assert sc.key == "test_dest"
    db.query(StorageConfig).filter_by(key="test_dest").delete()


def test_update_key(db: Session, storage_config, privacy_request):
    # Test happy path
    data: dict[str, Any] = {"key": "test_key", "name": "test name"}

    sc = storage_config.update(db, data=data)
    assert sc.key == "test_key"
    assert sc.name == "test name"

    data = {"key": None}

    # Test no path to create a key
    with pytest.raises(KeyValidationError) as exc:
        storage_config.update(db, data=data)
    assert str(exc.value) == "StorageConfig requires a name."

    # Test update on model with no key required
    assert hasattr(privacy_request, "key") is False
    privacy_request.update(db, data={"status": "complete"})
    assert "complete" == privacy_request.status.value


@pytest.mark.integration
class TestSaveKey:
    @pytest.mark.parametrize("key", ["bad key", "bad^key", "bad\\key"])
    def test_save_key_invalid_space(self, db: Session, storage_config, key):
        "Test prevent saving bad keys."
        storage_config.key = key
        with pytest.raises(KeyValidationError) as exc:
            storage_config.save(db)

        error_output = str(exc.value)
        expected_output = f"Key '{key}' on StorageConfig is invalid."
        print(error_output)
        assert error_output == expected_output

    def test_save_key_none(self, db: Session, storage_config):
        "Test key required on applicable models."
        storage_config.key = None
        with pytest.raises(KeyValidationError) as exc:
            storage_config.save(db)

        error_output = str(exc.value)
        expected_output = "Key 'None' on StorageConfig is invalid."
        print(error_output)
        assert error_output == expected_output

    def test_save_key_valid(self, db: Session, storage_config):
        "Test save with valid key"
        storage_config.key = "valid_key"
        storage_config.save(db)
        assert storage_config.key == "valid_key"

    def test_save_key_privacy_request(self, db: Session, privacy_request):
        # Test save on model with no key required
        assert hasattr(privacy_request, "key") is False
        privacy_request.status = "complete"
        privacy_request.save(db)
        assert "complete" == privacy_request.status.value  # type: ignore


def test_sanitize_key_replaces_invalid_chars() -> None:
    # Allowed characters are [A-Za-z0-9\-_]; everything else becomes '_'
    assert FidesBase.sanitize_key("valid_key-123") == "valid_key-123"
    # dots become underscores
    assert FidesBase.sanitize_key("has.dots") == "has_dots"
    # spaces and asterisks become underscores
    assert FidesBase.sanitize_key("bad*chars and spaces") == "bad_chars_and_spaces"
    # multiple consecutive invalid characters each replaced
    assert FidesBase.sanitize_key("a..b") == "a__b"
    # other invalid symbols become underscores
    assert FidesBase.sanitize_key("weird<>|chars") == "weird___chars"
