from unittest.mock import MagicMock

import pytest
from fideslang.models import Dataset as FideslangDataset
from fideslang.models import DatasetCollection, DatasetField

from fides.api.common_exceptions import ValidationError
from fides.api.models.connectionconfig import ConnectionType
from fides.service.dataset.validation_steps.saas import (
    _validate_saas_dataset_structure,
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


class TestValidateSaaSDatasetStructure:
    def _setup(self, endpoints, collections, existing_ctl_dataset=None):
        config_dict = _make_saas_config_dict(endpoints)
        connection_config = _make_connection_config(config_dict)
        dataset = _make_dataset("test_connector", collections)
        mock_db = _mock_db_with_existing_dataset(existing_ctl_dataset)
        return mock_db, connection_config, dataset

    def test_valid_dataset_passes(self):
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
        _validate_saas_dataset_structure(mock_db, connection_config, dataset)

    def test_adding_collection_rejected(self):
        mock_db, connection_config, dataset = self._setup(
            endpoints=[
                _make_endpoint("users", read_param_values=[]),
            ],
            collections=[
                {"name": "users", "fields": ["name"]},
                {"name": "extra_collection", "fields": ["foo"]},
            ],
        )
        with pytest.raises(ValidationError, match="Cannot add collections"):
            _validate_saas_dataset_structure(mock_db, connection_config, dataset)

    def test_removing_collection_rejected(self):
        mock_db, connection_config, dataset = self._setup(
            endpoints=[
                _make_endpoint("users", read_param_values=[]),
                _make_endpoint("orders", read_param_values=[]),
            ],
            collections=[
                {"name": "users", "fields": ["name"]},
            ],
        )
        with pytest.raises(ValidationError, match="Cannot remove collections"):
            _validate_saas_dataset_structure(mock_db, connection_config, dataset)

    def test_removing_referenced_field_rejected(self):
        """Fields with dataset references in the SaaS config cannot be deleted."""
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
        )
        with pytest.raises(ValidationError, match="Cannot delete field 'user_id'"):
            _validate_saas_dataset_structure(mock_db, connection_config, dataset)

    def test_removing_identity_field_allowed(self):
        """Identity-based fields are not protected — they come from the identity seed, not dataset references."""
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
        _validate_saas_dataset_structure(mock_db, connection_config, dataset)

    def test_adding_field_allowed(self):
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
        _validate_saas_dataset_structure(mock_db, connection_config, dataset)

    def test_removing_non_referenced_field_allowed(self):
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
        _validate_saas_dataset_structure(mock_db, connection_config, dataset)

    def test_removing_delete_referenced_field_rejected(self):
        """Fields referenced by delete requests are also protected."""
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
        )
        with pytest.raises(ValidationError, match="Cannot delete field 'user_id'"):
            _validate_saas_dataset_structure(mock_db, connection_config, dataset)


class TestValidateSaaSDatasetImmutableFields:
    """Tests that top-level dataset metadata cannot be changed."""

    def _make_existing_ctl_dataset(self):
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

    def test_unchanged_metadata_passes(self):
        existing = self._make_existing_ctl_dataset()
        mock_db = _mock_db_with_existing_dataset(existing)
        connection_config = _make_connection_config(
            _make_saas_config_dict([_make_endpoint("users", read_param_values=[])])
        )
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
            name="Test Connector Dataset",
            description="Original description",
        )
        _validate_saas_dataset_structure(mock_db, connection_config, dataset)

    def test_changing_name_rejected(self):
        existing = self._make_existing_ctl_dataset()
        mock_db = _mock_db_with_existing_dataset(existing)
        connection_config = _make_connection_config(
            _make_saas_config_dict([_make_endpoint("users", read_param_values=[])])
        )
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
            name="Changed Name",
            description="Original description",
        )
        with pytest.raises(
            ValidationError, match="Cannot modify 'name' on a SaaS dataset"
        ):
            _validate_saas_dataset_structure(mock_db, connection_config, dataset)

    def test_changing_description_rejected(self):
        existing = self._make_existing_ctl_dataset()
        mock_db = _mock_db_with_existing_dataset(existing)
        connection_config = _make_connection_config(
            _make_saas_config_dict([_make_endpoint("users", read_param_values=[])])
        )
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
            name="Test Connector Dataset",
            description="Changed description",
        )
        with pytest.raises(
            ValidationError, match="Cannot modify 'description' on a SaaS dataset"
        ):
            _validate_saas_dataset_structure(mock_db, connection_config, dataset)

    def test_new_dataset_skips_immutable_check(self):
        """When no existing dataset is found (new dataset), immutable field check is skipped."""
        mock_db = _mock_db_with_existing_dataset(None)
        connection_config = _make_connection_config(
            _make_saas_config_dict([_make_endpoint("users", read_param_values=[])])
        )
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
        )
        _validate_saas_dataset_structure(mock_db, connection_config, dataset)
