from typing import Any, Dict

import pytest
from sqlalchemy.orm import Session

from fides.api.ops.common_exceptions import StorageConfigValidationError
from fides.api.ops.models.storage import StorageConfig, default_storage_config
from fides.api.ops.schemas.storage.storage import (
    DEFAULT_STORAGE_KEY,
    FileNaming,
    ResponseFormat,
    S3AuthMethod,
    StorageDestination,
    StorageDetails,
    StorageSecrets,
    StorageType,
)
from fides.lib.db.base_class import KeyOrNameAlreadyExists


class TestStorageConfigModel:
    @pytest.fixture(scope="function")
    def storage_details_s3(self) -> Dict[str, str]:
        return {
            StorageDetails.BUCKET.value: "some bucket",
            StorageDetails.NAMING.value: "some naming",
            StorageDetails.MAX_RETRIES.value: 0,
            StorageDetails.AUTH_METHOD.value: S3AuthMethod.SECRET_KEYS.value,
        }

    @pytest.fixture(scope="function")
    def storage_incoming_one(self, storage_details_s3) -> StorageDestination:
        name = "test storage destination 1"
        storage_type = StorageType.s3
        return StorageDestination(
            name=name,
            type=storage_type,
            details=storage_details_s3,
            key=None,
            format=ResponseFormat.csv,
        )

    @pytest.fixture(scope="function")
    def storage_incoming_default(db: Session) -> StorageDestination:
        """
        A storage destination schema object for a default storage config
        to represent an incoming request payload
        """
        return StorageDestination(
            name="default storage config",
            key=DEFAULT_STORAGE_KEY,
            type=StorageType.local,
            is_default=True,
            format=ResponseFormat.json,
            details={
                StorageDetails.NAMING.value: FileNaming.request_id.value,
            },
        )

    def test_unique_key_constraint(
        self, db: Session, storage_config, storage_incoming_one
    ):
        """Test key not supplied, but name caused a key to be created matching an existing key"""
        storage_incoming_one.name = storage_config.name

        with pytest.raises(KeyOrNameAlreadyExists):
            StorageConfig.create_or_update(db=db, data=storage_incoming_one.dict())

    def test_create_storage_config(
        self,
        db: Session,
        storage_incoming_one,
        storage_details_s3,
    ):
        storage_config = StorageConfig.create_or_update(
            db=db, data=storage_incoming_one.dict()
        )

        assert storage_config.name == "test storage destination 1"
        assert storage_config.type == StorageType.s3
        assert storage_config.details == storage_details_s3
        assert storage_config.format == ResponseFormat.csv
        assert storage_config.key == "test_storage_destination_1"
        assert storage_config.secrets is None
        assert not storage_config.is_default

        storage_config.delete(db)

        # assert is_default can't be passed in when creating a non-default storage config
        data = storage_incoming_one.dict()
        data["is_default"] = True
        with pytest.raises(StorageConfigValidationError) as e:
            StorageConfig.create_or_update(db=db, data=data)
        assert (
            "`is_default` can only be set to true on the default storage policy"
            in str(e.value)
        )
        storage_config_db = StorageConfig.get_by(
            db=db, field="key", value=storage_config.key
        )
        assert not storage_config_db

    def test_create_default_storage_config(
        self,
        db: Session,
        storage_incoming_default,
    ):
        storage_config = StorageConfig.create_or_update(
            db=db, data=storage_incoming_default.dict()
        )

        assert storage_config.key == DEFAULT_STORAGE_KEY
        assert storage_config.format == ResponseFormat.json
        assert storage_config.secrets is None
        assert storage_config.is_default

        storage_config.delete(db)

        # assert is_default MUST be passed in when creating a default storage config
        data = storage_incoming_default.dict()
        data.pop("is_default")
        with pytest.raises(StorageConfigValidationError) as e:
            StorageConfig.create_or_update(db=db, data=data)
        assert (
            "`is_default` must be set to true if updating the default storage policy"
            in str(e.value)
        )
        storage_config_db = StorageConfig.get_by(
            db=db, field="key", value=storage_config.key
        )
        assert not storage_config_db

        data = storage_incoming_default.dict()
        data["is_default"] = False
        with pytest.raises(StorageConfigValidationError) as e:
            StorageConfig.create_or_update(db=db, data=data)
        assert (
            "`is_default` must be set to true if updating the default storage policy"
            in str(e.value)
        )
        storage_config_db = StorageConfig.get_by(
            db=db, field="key", value=storage_config.key
        )
        assert not storage_config_db

    def test_update_storage_config(self, db: Session, storage_config):
        data = storage_config.__dict__.copy()
        data["format"] = ResponseFormat.json

        storage_config = StorageConfig.create_or_update(db=db, data=data)

        assert storage_config.name == storage_config.name
        assert storage_config.type == storage_config.type
        assert storage_config.details == storage_config.details
        assert storage_config.format == ResponseFormat.json
        assert storage_config.key == storage_config.key

        storage_config.delete(db)

        data = storage_config.__dict__.copy()
        data["is_default"] = True
        with pytest.raises(StorageConfigValidationError) as e:
            storage_config = StorageConfig.create_or_update(db=db, data=data)
        assert (
            "`is_default` can only be set to true on the default storage policy"
            in str(e.value)
        )
        storage_config_db = StorageConfig.get_by(
            db=db, field="key", value=storage_config.key
        )
        assert not storage_config_db

    def test_update_storage_config_default(self, db: Session, storage_config_default):
        data = storage_config_default.__dict__.copy()
        data["is_default"] = False
        data[
            "format"
        ] = ResponseFormat.csv  # just changing some arbitrary attribute as a test
        with pytest.raises(StorageConfigValidationError) as e:
            StorageConfig.create_or_update(db=db, data=data)
        assert (
            "`is_default` must be set to true if updating the default storage policy"
            in str(e.value)
        )
        default_storage_config_db = StorageConfig.get_by(
            db=db, field="key", value=storage_config_default.key
        )

        # refresh from db to wipe changes to the object made locally
        db.refresh(default_storage_config_db)
        # assert the storage config has been reset back to the base state from the db
        assert default_storage_config_db.format == ResponseFormat.json

        # now confirm our update to response format goes through as long as
        # `is_default` stays `True`
        data["is_default"] = True
        storage_config_default_updated = StorageConfig.create_or_update(
            db=db, data=data
        )
        assert storage_config_default_updated.format == ResponseFormat.csv

    def test_update_storage_config_secrets(self, db: Session, storage_config):
        secrets = {
            StorageSecrets.AWS_ACCESS_KEY_ID.value: "1345234524",
            StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "23451345834789",
        }

        storage_config.set_secrets(db=db, storage_secrets=secrets)

        assert (
            storage_config.secrets[StorageSecrets.AWS_ACCESS_KEY_ID.value]
            == "1345234524"
        )
        assert (
            storage_config.secrets[StorageSecrets.AWS_SECRET_ACCESS_KEY.value]
            == "23451345834789"
        )

    def test_default_storage_retrieval(
        self, db: Session, storage_config_default: StorageConfig
    ):
        """
        Ensure our `default_storage_config` utility method works as expected
        Both in cases where the default exists in the db and in cases when it doesn't
        """
        # `storage_config_default` fixture creates the default config
        # in the db, so we should be able to retrieve it successfully here
        retrieved_config = default_storage_config(db)
        assert storage_config_default == retrieved_config

        # delete the default storage config in the db
        # and we should no longer get a populated object now
        storage_config_default.delete(db)
        retrieved_config = default_storage_config(db)
        assert not retrieved_config
