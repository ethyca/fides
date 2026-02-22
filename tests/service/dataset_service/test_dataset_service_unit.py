"""
Unit tests for DatasetService using mocked repositories.

These tests verify business logic without a database connection.
"""

from unittest.mock import MagicMock, create_autospec, patch

import pytest

from fides.service.dataset.dataset_service import (
    DatasetNotFoundException,
    DatasetService,
    LinkedDatasetException,
)
from fides.service.dataset.repositories import (
    SqlAlchemyDatasetConfigRepository,
    SqlAlchemyDatasetRepository,
)


@pytest.fixture
def mock_dataset_repo():
    return create_autospec(SqlAlchemyDatasetRepository, instance=True)


@pytest.fixture
def mock_dataset_config_repo():
    return create_autospec(SqlAlchemyDatasetConfigRepository, instance=True)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def dataset_service(mock_dataset_repo, mock_dataset_config_repo, mock_db):
    return DatasetService(
        dataset_repo=mock_dataset_repo,
        dataset_config_repo=mock_dataset_config_repo,
        db=mock_db,
    )


class TestGetDataset:
    def test_returns_dataset_when_found(self, dataset_service, mock_dataset_repo):
        mock_dataset = MagicMock(fides_key="test_ds")
        mock_dataset_repo.get_by_fides_key.return_value = mock_dataset

        result = dataset_service.get_dataset("test_ds")

        assert result is mock_dataset
        mock_dataset_repo.get_by_fides_key.assert_called_once_with("test_ds")

    def test_raises_when_not_found(self, dataset_service, mock_dataset_repo):
        mock_dataset_repo.get_by_fides_key.return_value = None

        with pytest.raises(DatasetNotFoundException) as exc_info:
            dataset_service.get_dataset("missing_ds")

        assert "missing_ds" in str(exc_info.value)
        mock_dataset_repo.get_by_fides_key.assert_called_once_with("missing_ds")


class TestCreateDataset:
    def test_creates_after_validation(self, dataset_service, mock_dataset_repo):
        mock_input = MagicMock()
        mock_input.model_dump.return_value = {"fides_key": "new_ds", "name": "New"}

        mock_created = MagicMock(fides_key="new_ds")
        mock_dataset_repo.create.return_value = mock_created

        with patch.object(dataset_service, "validate_dataset"):
            result = dataset_service.create_dataset(mock_input)

        assert result is mock_created
        mock_dataset_repo.create.assert_called_once_with(
            data={"fides_key": "new_ds", "name": "New"}
        )

    def test_validates_before_creating(self, dataset_service, mock_dataset_repo):
        mock_input = MagicMock()
        mock_input.model_dump.return_value = {}

        with patch.object(
            dataset_service, "validate_dataset", side_effect=Exception("invalid")
        ):
            with pytest.raises(Exception, match="invalid"):
                dataset_service.create_dataset(mock_input)

        mock_dataset_repo.create.assert_not_called()


class TestUpdateDataset:
    def test_updates_existing_dataset(self, dataset_service, mock_dataset_repo):
        mock_input = MagicMock()
        mock_input.fides_key = "existing_ds"
        mock_input.model_dump.return_value = {"fides_key": "existing_ds", "name": "Updated"}

        mock_existing = MagicMock(fides_key="existing_ds")
        mock_dataset_repo.get_by_fides_key.return_value = mock_existing

        mock_updated = MagicMock(fides_key="existing_ds")
        mock_dataset_repo.update.return_value = mock_updated

        with patch.object(dataset_service, "validate_dataset"):
            result = dataset_service.update_dataset(mock_input)

        assert result is mock_updated
        mock_dataset_repo.update.assert_called_once_with(
            mock_existing, data={"fides_key": "existing_ds", "name": "Updated"}
        )

    def test_raises_when_dataset_not_found(self, dataset_service, mock_dataset_repo):
        mock_input = MagicMock()
        mock_input.fides_key = "missing_ds"

        mock_dataset_repo.get_by_fides_key.return_value = None

        with patch.object(dataset_service, "validate_dataset"):
            with pytest.raises(DatasetNotFoundException) as exc_info:
                dataset_service.update_dataset(mock_input)

        assert "missing_ds" in str(exc_info.value)
        mock_dataset_repo.update.assert_not_called()


class TestDeleteDataset:
    def test_deletes_dataset_with_no_associations(
        self, dataset_service, mock_dataset_repo, mock_dataset_config_repo
    ):
        mock_dataset = MagicMock(fides_key="standalone_ds", id="ds_123")
        mock_dataset_repo.get_by_fides_key.return_value = mock_dataset
        mock_dataset_config_repo.get_configs_for_dataset.return_value = []

        result = dataset_service.delete_dataset("standalone_ds")

        assert result is mock_dataset
        mock_dataset_repo.delete.assert_called_once_with(mock_dataset)
        mock_dataset_config_repo.get_configs_for_dataset.assert_called_once_with(
            "ds_123"
        )

    def test_raises_when_dataset_not_found(
        self, dataset_service, mock_dataset_repo, mock_dataset_config_repo
    ):
        mock_dataset_repo.get_by_fides_key.return_value = None

        with pytest.raises(DatasetNotFoundException):
            dataset_service.delete_dataset("missing_ds")

        mock_dataset_repo.delete.assert_not_called()
        mock_dataset_config_repo.get_configs_for_dataset.assert_not_called()

    def test_raises_when_dataset_has_single_association(
        self, dataset_service, mock_dataset_repo, mock_dataset_config_repo
    ):
        mock_dataset = MagicMock(fides_key="linked_ds", id="ds_456")
        mock_dataset_repo.get_by_fides_key.return_value = mock_dataset

        mock_config = MagicMock()
        mock_config.connection_config.name = "Postgres Connection"
        mock_config.connection_config.key = "pg_conn"
        mock_config.connection_config.connection_type.value = "postgres"
        mock_config.connection_config.system_id = None
        mock_dataset_config_repo.get_configs_for_dataset.return_value = [mock_config]

        with pytest.raises(LinkedDatasetException) as exc_info:
            dataset_service.delete_dataset("linked_ds")

        error = str(exc_info.value)
        assert "Cannot delete dataset 'linked_ds'" in error
        assert "'Postgres Connection' (postgres)" in error
        assert "Remove the dataset from these integrations" in error
        mock_dataset_repo.delete.assert_not_called()

    def test_raises_when_dataset_has_multiple_associations(
        self, dataset_service, mock_dataset_repo, mock_dataset_config_repo
    ):
        mock_dataset = MagicMock(fides_key="multi_ds", id="ds_789")
        mock_dataset_repo.get_by_fides_key.return_value = mock_dataset

        pg_config = MagicMock()
        pg_config.connection_config.name = "Postgres"
        pg_config.connection_config.key = "pg"
        pg_config.connection_config.connection_type.value = "postgres"
        pg_config.connection_config.system_id = None

        mysql_config = MagicMock()
        mysql_config.connection_config.name = "MySQL"
        mysql_config.connection_config.key = "mysql"
        mysql_config.connection_config.connection_type.value = "mysql"
        mysql_config.connection_config.system_id = None

        mock_dataset_config_repo.get_configs_for_dataset.return_value = [
            pg_config,
            mysql_config,
        ]

        with pytest.raises(LinkedDatasetException) as exc_info:
            dataset_service.delete_dataset("multi_ds")

        error = str(exc_info.value)
        assert "'Postgres' (postgres)" in error
        assert "'MySQL' (mysql)" in error
        mock_dataset_repo.delete.assert_not_called()

    def test_includes_system_info_in_error(
        self, dataset_service, mock_dataset_repo, mock_dataset_config_repo
    ):
        mock_dataset = MagicMock(fides_key="sys_ds", id="ds_sys")
        mock_dataset_repo.get_by_fides_key.return_value = mock_dataset

        mock_system = MagicMock()
        mock_system.name = "Test System"
        mock_system.fides_key = "test_system"

        mock_config = MagicMock()
        mock_config.connection_config.name = "System Connection"
        mock_config.connection_config.key = "sys_conn"
        mock_config.connection_config.connection_type.value = "postgres"
        mock_config.connection_config.system_id = "sys_123"
        mock_config.connection_config.system = mock_system
        mock_dataset_config_repo.get_configs_for_dataset.return_value = [mock_config]

        with pytest.raises(LinkedDatasetException) as exc_info:
            dataset_service.delete_dataset("sys_ds")

        error = str(exc_info.value)
        assert "'System Connection' (postgres) in system 'Test System'" in error

    def test_uses_connection_key_when_name_missing(
        self, dataset_service, mock_dataset_repo, mock_dataset_config_repo
    ):
        mock_dataset = MagicMock(fides_key="key_ds", id="ds_key")
        mock_dataset_repo.get_by_fides_key.return_value = mock_dataset

        mock_config = MagicMock()
        mock_config.connection_config.name = None
        mock_config.connection_config.key = "fallback_key"
        mock_config.connection_config.connection_type.value = "postgres"
        mock_config.connection_config.system_id = None
        mock_dataset_config_repo.get_configs_for_dataset.return_value = [mock_config]

        with pytest.raises(LinkedDatasetException) as exc_info:
            dataset_service.delete_dataset("key_ds")

        assert "'fallback_key' (postgres)" in str(exc_info.value)


class TestUpsertDatasets:
    def test_inserts_new_datasets(
        self, dataset_service, mock_dataset_repo
    ):
        mock_ds1 = MagicMock()
        mock_ds1.fides_key = "new_ds_1"
        mock_ds1.model_dump.return_value = {"fides_key": "new_ds_1"}

        mock_ds2 = MagicMock()
        mock_ds2.fides_key = "new_ds_2"
        mock_ds2.model_dump.return_value = {"fides_key": "new_ds_2"}

        mock_dataset_repo.get_by_fides_key.return_value = None

        with patch.object(dataset_service, "validate_dataset"):
            mock_dataset_repo.create.return_value = MagicMock()
            inserted, updated = dataset_service.upsert_datasets([mock_ds1, mock_ds2])

        assert inserted == 2
        assert updated == 0

    def test_updates_existing_datasets(
        self, dataset_service, mock_dataset_repo
    ):
        mock_ds = MagicMock()
        mock_ds.fides_key = "existing_ds"
        mock_ds.model_dump.return_value = {"fides_key": "existing_ds", "name": "Updated"}

        mock_existing = MagicMock(fides_key="existing_ds")
        mock_dataset_repo.get_by_fides_key.return_value = mock_existing

        with patch.object(dataset_service, "validate_dataset"):
            inserted, updated = dataset_service.upsert_datasets([mock_ds])

        assert inserted == 0
        assert updated == 1
        mock_dataset_repo.update.assert_called_once_with(
            mock_existing, data={"fides_key": "existing_ds", "name": "Updated"}
        )

    def test_mixed_insert_and_update(
        self, dataset_service, mock_dataset_repo
    ):
        new_ds = MagicMock()
        new_ds.fides_key = "new"
        new_ds.model_dump.return_value = {"fides_key": "new"}

        existing_ds = MagicMock()
        existing_ds.fides_key = "existing"
        existing_ds.model_dump.return_value = {"fides_key": "existing"}

        mock_existing_obj = MagicMock(fides_key="existing")

        def side_effect(fides_key):
            if fides_key == "existing":
                return mock_existing_obj
            return None

        mock_dataset_repo.get_by_fides_key.side_effect = side_effect

        with patch.object(dataset_service, "validate_dataset"):
            mock_dataset_repo.create.return_value = MagicMock()
            inserted, updated = dataset_service.upsert_datasets(
                [new_ds, existing_ds]
            )

        assert inserted == 1
        assert updated == 1

    def test_reraises_on_error(self, dataset_service, mock_dataset_repo):
        mock_ds = MagicMock()
        mock_ds.fides_key = "bad_ds"

        mock_dataset_repo.get_by_fides_key.side_effect = RuntimeError("db error")

        with pytest.raises(RuntimeError, match="db error"):
            dataset_service.upsert_datasets([mock_ds])


class TestCleanDatasets:
    def test_delegates_to_repo_get_all(self, dataset_service, mock_dataset_repo, mock_db):
        mock_datasets = [MagicMock(), MagicMock()]
        mock_dataset_repo.get_all.return_value = mock_datasets

        with patch(
            "fides.service.dataset.dataset_service._run_clean_datasets",
            return_value=(["ds1", "ds2"], []),
        ) as mock_clean:
            succeeded, failed = dataset_service.clean_datasets()

        mock_dataset_repo.get_all.assert_called_once()
        mock_clean.assert_called_once_with(mock_db, mock_datasets)
        assert succeeded == ["ds1", "ds2"]
        assert failed == []
