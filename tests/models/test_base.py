import pytest
from sqlalchemy.orm import Session

from fidesops.common_exceptions import KeyValidationError
from fidesops.models.storage import StorageConfig
from fidesops.db.base_class import get_key_from_data


def test_get_key_from_data_method() -> None:
    # Test key in data
    key = get_key_from_data({"key": "test_key", "name": "config name"}, "StorageConfig")
    assert key == "test_key"

    # Test no key
    key = get_key_from_data({"name": "config name"}, "StorageConfig")
    assert key == "config_name"

    # Test no data
    with pytest.raises(KeyValidationError) as exc:
        get_key_from_data({}, "StorageConfig")
    assert str(exc.value) == "StorageConfig requires a name."

    # Test key not valid
    with pytest.raises(ValueError) as exc:
        get_key_from_data({"key": "test-key", "name": "config name"}, "StorageConfig")
    assert (
        str(exc.value)
        == "FidesKey must only contain alphanumeric characters, '.' or '_'."
    )


def test_create_key(db: Session):
    # Test no way to create a key
    with pytest.raises(KeyValidationError) as exc:
        StorageConfig.create(
            db,
            data={
                "type": "s3",
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
            "type": "s3",
            "details": {
                "bucket": "some-bucket",
                "object_name": "requests",
                "naming": "some-filename-convention-enum",
                "max_retries": 10,
            },
        },
    )

    assert sc.key == "test_dest"
    db.query(StorageConfig).filter_by(key="test_dest").delete()


def test_update_key(db: Session, storage_config, privacy_request):
    # Test happy path
    data = {"key": "test_key", "name": "test name"}

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


def test_save_key(db: Session, storage_config, privacy_request):
    # Test prevent saving bad keys.
    storage_config.key = "bad key"
    with pytest.raises(KeyValidationError) as exc:
        storage_config.save(db)

    assert str(exc.value) == "Key 'bad key' on StorageConfig is invalid."

    # Test key required on applicable models
    storage_config.key = None
    with pytest.raises(KeyValidationError) as exc:
        storage_config.save(db)

    assert str(exc.value) == "Key 'None' on StorageConfig is invalid."

    # Test save with valid key
    storage_config.key = "valid_key"
    storage_config.save(db)
    assert storage_config.key == "valid_key"

    # Test save on model with no key required
    assert hasattr(privacy_request, "key") is False
    privacy_request.status = "complete"
    privacy_request.save(db)
    assert "complete" == privacy_request.status.value
