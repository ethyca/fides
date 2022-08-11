from typing import Dict

import pytest
from fideslib.db.base_class import KeyOrNameAlreadyExists
from sqlalchemy.orm import Session

from fidesops.ops.models.storage import StorageConfig
from fidesops.ops.schemas.storage.storage import (
    ResponseFormat,
    StorageDestination,
    StorageDetails,
    StorageSecrets,
    StorageType,
)


class TestStorageConfigModel:
    @pytest.fixture(scope="function")
    def storage_details_s3(self) -> Dict[str, str]:
        return {
            StorageDetails.BUCKET.value: "some bucket",
            StorageDetails.NAMING.value: "some naming",
            StorageDetails.OBJECT_NAME.value: "some object name",
            StorageDetails.MAX_RETRIES.value: 0,
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

        storage_config.delete(db)

    def test_update_storage_config(self, db: Session, storage_config):
        data = storage_config.__dict__
        data["format"] == ResponseFormat.json

        storage_config = StorageConfig.create_or_update(db=db, data=data)

        assert storage_config.name == storage_config.name
        assert storage_config.type == storage_config.type
        assert storage_config.details == storage_config.details
        assert storage_config.format == ResponseFormat.json
        assert storage_config.key == storage_config.key

        storage_config.delete(db)

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
