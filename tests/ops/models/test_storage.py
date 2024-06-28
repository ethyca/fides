from typing import Dict

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.db.base_class import KeyOrNameAlreadyExists
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.storage import (
    StorageConfig,
    default_storage_config_name,
    get_active_default_storage_config,
    get_default_storage_config_by_type,
)
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    FileNaming,
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
            StorageDetails.MAX_RETRIES.value: 0,
            StorageDetails.AUTH_METHOD.value: AWSAuthMethod.SECRET_KEYS.value,
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
            type=StorageType.local,
            is_default=True,
            format=ResponseFormat.json,
            details={
                StorageDetails.NAMING.value: FileNaming.request_id.value,
            },
        )

    @pytest.fixture(scope="function")
    def default_local_storage_config(db: Session) -> StorageConfig:
        """
        An example default local StorageCong
        """
        return StorageConfig(
            name="A sample default local storage config",
            key="sample_default_local_storage",
            type=StorageType.local,
            is_default=True,
            format=ResponseFormat.json,
            details={
                StorageDetails.NAMING.value: FileNaming.request_id.value,
            },
        )

    @pytest.fixture(scope="function")
    def another_default_local_storage_config(db: Session) -> StorageConfig:
        """
        An example default local StorageCong
        """
        return StorageConfig(
            name="Another default local storage config",
            key="another_default_local_storage",
            type=StorageType.local,
            is_default=True,
            format=ResponseFormat.json,
            details={
                StorageDetails.NAMING.value: FileNaming.request_id.value,
            },
        )

    def test_only_one_default_per_type(
        self,
        db: Session,
        default_local_storage_config: StorageConfig,
        another_default_local_storage_config: StorageConfig,
    ):
        default_local_storage_config.save(db)
        initial_num_configs = len(StorageConfig.all(db))
        # we should hit the database constraint that doesn't allow us to
        #  create more than one default per storage config type
        with pytest.raises(IntegrityError) as e:
            another_default_local_storage_config.save(db)
        assert "violates unique constraint" in (str(e))
        assert len(StorageConfig.all(db)) == initial_num_configs

        # but we should be able to add if it's not a default
        another_default_local_storage_config.is_default = False
        another_default_local_storage_config.save(db)
        # assert it was successfully added
        assert len(StorageConfig.all(db)) == initial_num_configs + 1

    def test_unique_key_constraint(
        self, db: Session, storage_config, storage_incoming_one
    ):
        """Test key not supplied, but name caused a key to be created matching an existing key"""
        storage_incoming_one.name = storage_config.name

        with pytest.raises(KeyOrNameAlreadyExists):
            StorageConfig.create_or_update(
                db=db, data=storage_incoming_one.model_dump(mode="json")
            )

    def test_create_storage_config(
        self,
        db: Session,
        storage_incoming_one,
        storage_details_s3,
    ):
        storage_config = StorageConfig.create_or_update(
            db=db, data=storage_incoming_one.model_dump(mode="json")
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
        data["format"] = ResponseFormat.json

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

    def test_default_storage_by_type(
        self, db: Session, storage_config_default: StorageConfig
    ):
        """
        Ensure our `default_storage_config` utility method works as expected
        Both in cases where the default exists in the db and in cases when it doesn't
        """
        # `storage_config_default` fixture creates the default config
        # in the db, so we should be able to retrieve it successfully here
        retrieved_config = get_default_storage_config_by_type(
            db, storage_config_default.type
        )
        assert storage_config_default == retrieved_config

        # delete the default storage config in the db
        # and we should no longer get a populated object now
        storage_config_default.delete(db)
        retrieved_config = get_default_storage_config_by_type(
            db, storage_config_default.type
        )
        assert not retrieved_config

        # assert unconfigured default storage is not returned since we only have a default
        # s3 storage with this fixture
        retrieved_config = get_default_storage_config_by_type(db, StorageType.gcs)
        assert not retrieved_config

        # assert passing a nonexisting storage type doesn't work
        # s3 storage with this fixture
        with pytest.raises(ValueError) as e:
            retrieved_config = get_default_storage_config_by_type(
                db, "some-madeup-storage-type"
            )

        assert "must be a valid StorageType enum member" in str(e)

    def test_active_default_storage_retrieval(
        self, db: Session, storage_config_default: StorageConfig
    ):
        """
        Ensure our `active_default_storage_config` utility method works as expected
        """
        # `storage_config_default` fixture creates a default s3 config
        # but until we've updated the appropriate settings in the API
        # a local storage config is returned as our active default
        retrieved_config = get_active_default_storage_config(db)
        assert retrieved_config.type == StorageType.local
        assert retrieved_config.name == default_storage_config_name(
            StorageType.local.value
        )
        assert retrieved_config.is_default
        assert retrieved_config == get_default_storage_config_by_type(
            db, StorageType.local.value
        )

        # now we mimic setting the active default storage type in the API
        # and we should get back the default s3 storage config created in the fixture
        ApplicationConfig.create_or_update(
            db,
            data={
                "api_set": {
                    "storage": {"active_default_storage_type": StorageType.s3.value}
                }
            },
        )
        retrieved_config = get_active_default_storage_config(db)
        assert retrieved_config == storage_config_default

        # delete the default storage config in the db
        # and we should get back an empty storage config, because we're still set to use s3
        storage_config_default.delete(db)
        retrieved_config = get_active_default_storage_config(db)
        assert retrieved_config is None

        # mimic setting active default back to `local` via API
        # and we should get back the local default config
        ApplicationConfig.create_or_update(
            db,
            data={
                "api_set": {
                    "storage": {"active_default_storage_type": StorageType.local.value}
                }
            },
        )
        retrieved_config = get_active_default_storage_config(db)
        assert retrieved_config.type == StorageType.local
        assert retrieved_config.name == default_storage_config_name(
            StorageType.local.value
        )
        assert retrieved_config.is_default
        assert retrieved_config == get_default_storage_config_by_type(
            db, StorageType.local
        )

    def test_format_validator(self):
        """
        Test the custom root validator that restricts certain formats for local destinations.
        """

        # No exceptions should be raised for valid local destination
        assert StorageDestination(
            name="Local destination",
            type=StorageType.local.value,
            format=ResponseFormat.json.value,
            details={StorageDetails.NAMING.value: FileNaming.request_id.value},
        )

        assert StorageDestination(
            name="Local destination",
            type=StorageType.local.value,
            format=ResponseFormat.html.value,
            details={StorageDetails.NAMING.value: FileNaming.request_id.value},
        )

        # Expect ValueError for invalid local destination
        with pytest.raises(ValueError) as e:
            StorageDestination(
                name="Local destination",
                type=StorageType.local.value,
                format=ResponseFormat.csv.value,
                details={StorageDetails.NAMING.value: FileNaming.request_id.value},
            )
        assert (
            "Value error, Only JSON or HTML upload format are supported for local storage destinations."
            in str(e._excinfo[1])
        )
