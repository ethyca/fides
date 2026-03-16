from unittest.mock import MagicMock

from fideslang.models import Dataset as FideslangDataset
from fideslang.models import DatasetCollection, DatasetField

from fides.api.models.connectionconfig import ConnectionType
from fides.service.dataset.validation_steps.saas import (
    _restore_immutable_fields,
    _restore_protected_structure,
)


def _make_saas_config_dict(endpoints: list[dict]) -> dict:
    """Build a minimal saas_config dict with the given endpoints."""
    return {
        "fides_key": "test_connector",
        "name": "Test Connector",
        "type": "custom",
        "description": "test",
        "version": "0.0.1",
        "connector_params": [{"name": "domain"}, {"name": "api_key"}],
        "client_config": {
            "protocol": "https",
            "host": "<domain>",
            "authentication": {
                "strategy": "bearer",
                "configuration": {"token": "<api_key>"},
            },
        },
        "test_request": {"method": "GET", "path": "/test"},
        "endpoints": endpoints,
    }


def _make_endpoint(
    name: str,
    read_param_values: list[dict] | None = None,
    delete_param_values: list[dict] | None = None,
) -> dict:
    """Build a minimal endpoint dict."""
    requests = {}
    if read_param_values is not None:
        requests["read"] = {
            "method": "GET",
            "path": f"/{name}",
            "param_values": read_param_values,
        }
    if delete_param_values is not None:
        requests["delete"] = {
            "method": "DELETE",
            "path": f"/{name}",
            "param_values": delete_param_values,
        }
    return {"name": name, "requests": requests}


def _make_connection_config(saas_config_dict: dict) -> MagicMock:
    """Create a mock ConnectionConfig with the given saas_config."""
    mock = MagicMock()
    mock.saas_config = saas_config_dict
    mock.key = "test_connector"
    mock.connection_type = ConnectionType.saas
    return mock


def _make_dataset(
    fides_key: str, collections: list[dict], **kwargs
) -> FideslangDataset:
    """Build a FideslangDataset from a simplified structure."""
    dataset_collections = []
    for col in collections:
        fields = [DatasetField(name=f_name) for f_name in col.get("fields", [])]
        dataset_collections.append(DatasetCollection(name=col["name"], fields=fields))
    return FideslangDataset(
        fides_key=fides_key,
        name=kwargs.get("name", fides_key),
        description=kwargs.get("description", "test dataset"),
        organization_fides_key=kwargs.get(
            "organization_fides_key", "default_organization"
        ),
        collections=dataset_collections,
    )


def _make_dataset_reference(collection: str, field: str) -> dict:
    """Build a param_value with a FidesDatasetReference."""
    return {
        "name": field,
        "references": [
            {
                "dataset": "<instance_fides_key>",
                "field": f"{collection}.{field}",
                "direction": "from",
            }
        ],
    }


def _mock_db_with_existing_dataset(existing_dataset=None):
    """Create a mock db session that returns the given dataset from a query."""
    mock_db = MagicMock()
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = existing_dataset
    return mock_db


def _make_existing_ctl_dataset():
    """Mock a CtlDataset ORM object that FideslangDataset.model_validate can read."""
    mock = MagicMock()
    mock.fides_key = "test_connector"
    mock.name = "Test Connector Dataset"
    mock.description = "Original description"
    mock.organization_fides_key = "default_organization"
    mock.collections = []
    mock.meta = None
    mock.data_categories = None
    mock.fides_meta = None
    mock.data_qualifier = None
    return mock


def _make_existing_ctl_dataset_with_collections(collections: list[dict]):
    """Mock a CtlDataset with collections for restoration tests."""
    mock = _make_existing_ctl_dataset()
    mock_collections = []
    for col in collections:
        mock_col = MagicMock()
        mock_col.name = col["name"]
        mock_fields = []
        for f_name in col.get("fields", []):
            mock_field = MagicMock()
            mock_field.name = f_name
            mock_field.description = None
            mock_field.data_categories = None
            mock_field.data_qualifier = None
            mock_field.fides_meta = None
            mock_field.fields = None
            mock_field.retention = None
            mock_fields.append(mock_field)
        mock_col.fields = mock_fields
        mock_col.description = None
        mock_col.data_categories = None
        mock_col.fides_meta = None
        mock_col.data_qualifier = None
        mock_collections.append(mock_col)
    mock.collections = mock_collections
    return mock


class TestRestoreProtectedStructure:
    def _setup(self, endpoints, collections, existing_ctl_dataset=None):
        config_dict = _make_saas_config_dict(endpoints)
        connection_config = _make_connection_config(config_dict)
        dataset = _make_dataset("test_connector", collections)
        mock_db = _mock_db_with_existing_dataset(existing_ctl_dataset)
        return mock_db, connection_config, dataset

    def test_valid_dataset_no_warnings(self):
        mock_db, connection_config, dataset = self._setup(
            endpoints=[
                _make_endpoint(
                    "users",
                    read_param_values=[
                        _make_dataset_reference("users", "user_id"),
                    ],
                ),
                _make_endpoint("orders", read_param_values=[]),
            ],
            collections=[
                {"name": "users", "fields": ["user_id", "name", "email"]},
                {"name": "orders", "fields": ["order_id"]},
            ],
        )
        warnings = _restore_protected_structure(mock_db, connection_config, dataset)
        assert warnings == []

    def test_added_collection_removed_with_warning(self):
        mock_db, connection_config, dataset = self._setup(
            endpoints=[
                _make_endpoint("users", read_param_values=[]),
            ],
            collections=[
                {"name": "users", "fields": ["name"]},
                {"name": "extra_collection", "fields": ["foo"]},
            ],
        )
        warnings = _restore_protected_structure(mock_db, connection_config, dataset)
        assert len(warnings) == 1
        assert warnings[0].collection == "extra_collection"
        assert "Removed" in warnings[0].message
        # The extra collection should have been removed
        assert {col.name for col in dataset.collections} == {"users"}

    def test_removed_collection_restored_with_warning(self):
        existing = _make_existing_ctl_dataset_with_collections(
            [
                {"name": "users", "fields": ["name"]},
                {"name": "orders", "fields": ["order_id"]},
            ]
        )
        mock_db, connection_config, dataset = self._setup(
            endpoints=[
                _make_endpoint("users", read_param_values=[]),
                _make_endpoint("orders", read_param_values=[]),
            ],
            collections=[
                {"name": "users", "fields": ["name"]},
            ],
            existing_ctl_dataset=existing,
        )
        warnings = _restore_protected_structure(mock_db, connection_config, dataset)
        assert len(warnings) == 1
        assert warnings[0].collection == "orders"
        assert "Restored" in warnings[0].message
        assert {col.name for col in dataset.collections} == {"users", "orders"}

    def test_deleted_referenced_field_restored_with_warning(self):
        existing = _make_existing_ctl_dataset_with_collections(
            [{"name": "users", "fields": ["user_id", "name", "email"]}]
        )
        mock_db, connection_config, dataset = self._setup(
            endpoints=[
                _make_endpoint(
                    "users",
                    read_param_values=[
                        _make_dataset_reference("users", "user_id"),
                    ],
                ),
            ],
            collections=[
                {"name": "users", "fields": ["name", "email"]},
            ],
            existing_ctl_dataset=existing,
        )
        warnings = _restore_protected_structure(mock_db, connection_config, dataset)
        assert len(warnings) == 1
        assert warnings[0].collection == "users"
        assert warnings[0].field == "user_id"
        assert "Restored" in warnings[0].message
        # user_id should be restored
        users_collection = next(c for c in dataset.collections if c.name == "users")
        assert {f.name for f in users_collection.fields} == {
            "name",
            "email",
            "user_id",
        }

    def test_removing_identity_field_allowed_no_warning(self):
        mock_db, connection_config, dataset = self._setup(
            endpoints=[
                _make_endpoint(
                    "users",
                    read_param_values=[
                        {"name": "user_id", "identity": "email"},
                    ],
                ),
            ],
            collections=[
                {"name": "users", "fields": ["name"]},
            ],
        )
        warnings = _restore_protected_structure(mock_db, connection_config, dataset)
        assert warnings == []

    def test_adding_field_allowed_no_warning(self):
        mock_db, connection_config, dataset = self._setup(
            endpoints=[
                _make_endpoint(
                    "users",
                    read_param_values=[
                        _make_dataset_reference("users", "user_id"),
                    ],
                ),
            ],
            collections=[
                {"name": "users", "fields": ["user_id", "name", "extra_field"]},
            ],
        )
        warnings = _restore_protected_structure(mock_db, connection_config, dataset)
        assert warnings == []

    def test_removing_non_referenced_field_allowed_no_warning(self):
        mock_db, connection_config, dataset = self._setup(
            endpoints=[
                _make_endpoint(
                    "users",
                    read_param_values=[
                        _make_dataset_reference("users", "user_id"),
                    ],
                ),
            ],
            collections=[
                {"name": "users", "fields": ["user_id"]},
            ],
        )
        warnings = _restore_protected_structure(mock_db, connection_config, dataset)
        assert warnings == []

    def test_delete_referenced_field_restored_with_warning(self):
        existing = _make_existing_ctl_dataset_with_collections(
            [{"name": "users", "fields": ["user_id", "name"]}]
        )
        mock_db, connection_config, dataset = self._setup(
            endpoints=[
                _make_endpoint(
                    "users",
                    delete_param_values=[
                        _make_dataset_reference("users", "user_id"),
                    ],
                ),
            ],
            collections=[
                {"name": "users", "fields": ["name"]},
            ],
            existing_ctl_dataset=existing,
        )
        warnings = _restore_protected_structure(mock_db, connection_config, dataset)
        assert len(warnings) == 1
        assert warnings[0].collection == "users"
        assert warnings[0].field == "user_id"


class TestRestoreImmutableFields:
    def test_unchanged_metadata_no_warnings(self):
        existing = _make_existing_ctl_dataset()
        mock_db = _mock_db_with_existing_dataset(existing)
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
            name="Test Connector Dataset",
            description="Original description",
        )
        warnings = _restore_immutable_fields(mock_db, dataset)
        assert warnings == []

    def test_changed_name_restored_with_warning(self):
        existing = _make_existing_ctl_dataset()
        mock_db = _mock_db_with_existing_dataset(existing)
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
            name="Changed Name",
            description="Original description",
        )
        warnings = _restore_immutable_fields(mock_db, dataset)
        assert len(warnings) == 1
        assert warnings[0].collection is None
        assert warnings[0].field == "name"
        assert "'name'" in warnings[0].message
        assert dataset.name == "Test Connector Dataset"

    def test_changed_description_restored_with_warning(self):
        existing = _make_existing_ctl_dataset()
        mock_db = _mock_db_with_existing_dataset(existing)
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
            name="Test Connector Dataset",
            description="Changed description",
        )
        warnings = _restore_immutable_fields(mock_db, dataset)
        assert len(warnings) == 1
        assert "'description'" in warnings[0].message
        assert dataset.description == "Original description"

    def test_multiple_fields_changed_multiple_warnings(self):
        existing = _make_existing_ctl_dataset()
        mock_db = _mock_db_with_existing_dataset(existing)
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
            name="Changed Name",
            description="Changed description",
        )
        warnings = _restore_immutable_fields(mock_db, dataset)
        assert len(warnings) == 2
        assert dataset.name == "Test Connector Dataset"
        assert dataset.description == "Original description"

    def test_new_dataset_skips_immutable_check(self):
        mock_db = _mock_db_with_existing_dataset(None)
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
        )
        warnings = _restore_immutable_fields(mock_db, dataset)
        assert warnings == []
