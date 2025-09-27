import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.models.sql_models import System
from fides.service.dataset.dataset_service import (
    DatasetNotFoundException,
    DatasetService,
    LinkedDatasetException,
)


@pytest.fixture
def dataset_service(db: Session) -> DatasetService:
    return DatasetService(db)


class TestDatasetServiceDeleteDataset:
    """Test the DatasetService.delete_dataset method, focusing on the new validation logic"""

    def test_delete_dataset_not_found(
        self, db: Session, dataset_service: DatasetService
    ):
        """Test that deleting a non-existent dataset raises DatasetNotFoundException"""
        with pytest.raises(DatasetNotFoundException) as exc_info:
            dataset_service.delete_dataset("nonexistent_dataset")

        assert "No CTL dataset found with fides_key 'nonexistent_dataset'" in str(
            exc_info.value
        )

    def test_delete_dataset_success_no_associations(
        self, db: Session, dataset_service: DatasetService
    ):
        """Test successful deletion of a dataset with no DatasetConfig associations"""
        # Create a standalone dataset
        dataset_data = {
            "fides_key": "standalone_dataset",
            "name": "Standalone Dataset",
            "description": "A dataset with no integrations",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "integer"},
                        }
                    ],
                }
            ],
        }
        dataset = CtlDataset.create(db, data=dataset_data)

        # Delete the dataset - should succeed
        deleted_dataset = dataset_service.delete_dataset("standalone_dataset")

        assert deleted_dataset.fides_key == "standalone_dataset"
        assert (
            CtlDataset.get_by(db, field="fides_key", value="standalone_dataset") is None
        )

    def test_delete_dataset_with_single_association(
        self, db: Session, dataset_service: DatasetService
    ):
        """Test deletion fails when dataset is associated to a single DatasetConfig"""
        # Create a dataset
        dataset_data = {
            "fides_key": "associated_dataset",
            "name": "Associated Dataset",
            "description": "A dataset with integration associations",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "integer"},
                        }
                    ],
                }
            ],
        }
        dataset = CtlDataset.create(db, data=dataset_data)

        # Create a connection config
        connection_data = {
            "key": "test_postgres_connection",
            "name": "Test Postgres Connection",
            "connection_type": ConnectionType.postgres,
            "access": "write",
        }
        connection_config = ConnectionConfig.create(db, data=connection_data)

        # Create a DatasetConfig that references the dataset
        dataset_config_data = {
            "connection_config_id": connection_config.id,
            "fides_key": "test_dataset_config",
            "ctl_dataset_id": dataset.id,
        }
        DatasetConfig.create(db, data=dataset_config_data)

        # Attempt to delete - should fail
        with pytest.raises(LinkedDatasetException) as exc_info:
            dataset_service.delete_dataset("associated_dataset")

        error = exc_info.value
        expected_message = (
            "Cannot delete dataset 'associated_dataset' because it is associated with "
            "the following integration(s): 'Test Postgres Connection' (postgres). "
            "Remove the dataset from these integrations before deleting."
        )
        assert str(error) == expected_message

    def test_delete_dataset_with_multiple_associations(
        self, db: Session, dataset_service: DatasetService
    ):
        """Test deletion fails when dataset is associated to multiple DatasetConfigs"""
        # Create a dataset
        dataset_data = {
            "fides_key": "multi_associated_dataset",
            "name": "Multi Associated Dataset",
            "description": "A dataset with multiple integration associations",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "integer"},
                        }
                    ],
                }
            ],
        }
        dataset = CtlDataset.create(db, data=dataset_data)

        # Create multiple connection configs
        postgres_connection_data = {
            "key": "postgres_connection",
            "name": "Postgres Connection",
            "connection_type": ConnectionType.postgres,
            "access": "write",
        }
        postgres_config = ConnectionConfig.create(db, data=postgres_connection_data)

        mysql_connection_data = {
            "key": "mysql_connection",
            "name": "MySQL Connection",
            "connection_type": ConnectionType.mysql,
            "access": "read",
        }
        mysql_config = ConnectionConfig.create(db, data=mysql_connection_data)

        # Create DatasetConfigs for both connections
        postgres_dataset_config = {
            "connection_config_id": postgres_config.id,
            "fides_key": "postgres_dataset_config",
            "ctl_dataset_id": dataset.id,
        }
        DatasetConfig.create(db, data=postgres_dataset_config)

        mysql_dataset_config = {
            "connection_config_id": mysql_config.id,
            "fides_key": "mysql_dataset_config",
            "ctl_dataset_id": dataset.id,
        }
        DatasetConfig.create(db, data=mysql_dataset_config)

        # Attempt to delete - should fail with both integrations listed
        with pytest.raises(LinkedDatasetException) as exc_info:
            dataset_service.delete_dataset("multi_associated_dataset")

        error = exc_info.value
        expected_message = (
            "Cannot delete dataset 'multi_associated_dataset' because it is associated with "
            "the following integration(s): 'Postgres Connection' (postgres), 'MySQL Connection' (mysql). "
            "Remove the dataset from these integrations before deleting."
        )
        assert str(error) == expected_message

    def test_delete_dataset_with_system_information(
        self, db: Session, dataset_service: DatasetService
    ):
        """Test that system information is included in error when available"""
        # Create a system
        system_data = {
            "fides_key": "test_system",
            "name": "Test System",
            "system_type": "Service",
        }
        system = System.create(db, data=system_data)

        # Create a dataset
        dataset_data = {
            "fides_key": "system_dataset",
            "name": "System Dataset",
            "description": "A dataset associated with a system",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "integer"},
                        }
                    ],
                }
            ],
        }
        dataset = CtlDataset.create(db, data=dataset_data)

        # Create a connection config with system association
        connection_data = {
            "key": "system_connection",
            "name": "System Connection",
            "connection_type": ConnectionType.postgres,
            "access": "write",
            "system_id": system.id,
        }
        connection_config = ConnectionConfig.create(db, data=connection_data)

        # Create a DatasetConfig
        dataset_config_data = {
            "connection_config_id": connection_config.id,
            "fides_key": "system_dataset_config",
            "ctl_dataset_id": dataset.id,
        }
        DatasetConfig.create(db, data=dataset_config_data)

        # Attempt to delete - should fail with system information included
        with pytest.raises(LinkedDatasetException) as exc_info:
            dataset_service.delete_dataset("system_dataset")

        error = exc_info.value
        expected_message = (
            "Cannot delete dataset 'system_dataset' because it is associated with "
            "the following integration(s): 'System Connection' (postgres) in system 'Test System'. "
            "Remove the dataset from these integrations before deleting."
        )
        assert str(error) == expected_message

    def test_delete_dataset_connection_config_without_name(
        self, db: Session, dataset_service: DatasetService
    ):
        """Test that connection key is used when connection name is not available"""
        # Create a dataset
        dataset_data = {
            "fides_key": "no_name_dataset",
            "name": "No Name Dataset",
            "description": "A dataset with unnamed connection",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "integer"},
                        }
                    ],
                }
            ],
        }
        dataset = CtlDataset.create(db, data=dataset_data)

        # Create a connection config without a name
        connection_data = {
            "key": "no_name_connection",
            "connection_type": ConnectionType.postgres,
            "access": "write",
        }
        connection_config = ConnectionConfig.create(db, data=connection_data)

        # Create a DatasetConfig
        dataset_config_data = {
            "connection_config_id": connection_config.id,
            "fides_key": "no_name_dataset_config",
            "ctl_dataset_id": dataset.id,
        }
        DatasetConfig.create(db, data=dataset_config_data)

        # Attempt to delete - should use connection key as name
        with pytest.raises(LinkedDatasetException) as exc_info:
            dataset_service.delete_dataset("no_name_dataset")

        error = exc_info.value
        expected_message = (
            "Cannot delete dataset 'no_name_dataset' because it is associated with "
            "the following integration(s): 'no_name_connection' (postgres). "
            "Remove the dataset from these integrations before deleting."
        )
        assert str(error) == expected_message
