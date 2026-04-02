from unittest.mock import MagicMock

from fideslang.models import Dataset as FideslangDataset
from fideslang.models import DatasetCollection, DatasetField

from fides.api.models.connectionconfig import ConnectionType
from fides.service.dataset.validation_steps.saas import (
    _resolve_field_path,
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


def _make_fields(field_specs) -> list[DatasetField]:
    """Build DatasetField objects from a spec.

    *field_specs* can be:
      - a list of plain strings  (flat fields, no children)
      - a list of dicts like ``{"name": "address", "fields": ["street", "city"]}``
    """
    result = []
    for spec in field_specs:
        if isinstance(spec, str):
            result.append(DatasetField(name=spec))
        else:
            children = _make_fields(spec.get("fields", []))
            result.append(DatasetField(name=spec["name"], fields=children or None))
    return result


def _make_dataset(
    fides_key: str, collections: list[dict], **kwargs
) -> FideslangDataset:
    """Build a FideslangDataset from a simplified structure."""
    dataset_collections = []
    for col in collections:
        fields = _make_fields(col.get("fields", []))
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


def _make_existing_dataset(
    collections: list[dict] | None = None,
    name: str = "Test Connector Dataset",
    description: str = "Original description",
) -> FideslangDataset:
    """Build a FideslangDataset to act as the existing dataset."""
    cols = collections or []
    return _make_dataset(
        "test_connector",
        cols,
        name=name,
        description=description,
    )


class TestResolveFieldPath:
    """Tests for the _resolve_field_path helper."""

    def test_top_level_field(self):
        fields = _make_fields(["user_id", "name"])
        assert _resolve_field_path(fields, "user_id") is not None
        assert _resolve_field_path(fields, "user_id").name == "user_id"

    def test_missing_top_level_field(self):
        fields = _make_fields(["name"])
        assert _resolve_field_path(fields, "user_id") is None

    def test_nested_field(self):
        fields = _make_fields(
            [
                {"name": "address", "fields": ["street", "city"]},
            ]
        )
        resolved = _resolve_field_path(fields, "address.street")
        assert resolved is not None
        assert resolved.name == "street"

    def test_missing_nested_field(self):
        fields = _make_fields(
            [
                {"name": "address", "fields": ["city"]},
            ]
        )
        assert _resolve_field_path(fields, "address.street") is None

    def test_missing_intermediate(self):
        fields = _make_fields(["name"])
        assert _resolve_field_path(fields, "address.street") is None

    def test_deeply_nested_field(self):
        fields = _make_fields(
            [
                {
                    "name": "address",
                    "fields": [
                        {"name": "geo", "fields": ["lat", "lng"]},
                    ],
                },
            ]
        )
        resolved = _resolve_field_path(fields, "address.geo.lat")
        assert resolved is not None
        assert resolved.name == "lat"

    def test_empty_fields_list(self):
        assert _resolve_field_path([], "anything") is None


class TestRestoreProtectedStructure:
    def _setup(self, endpoints, collections, existing_dataset=None):
        config_dict = _make_saas_config_dict(endpoints)
        connection_config = _make_connection_config(config_dict)
        dataset = _make_dataset("test_connector", collections)
        return connection_config, dataset, existing_dataset

    def test_valid_dataset_no_warnings(self):
        connection_config, dataset, existing = self._setup(
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
        warnings = _restore_protected_structure(connection_config, dataset, existing)
        assert warnings == []

    def test_added_collection_removed_with_warning(self):
        connection_config, dataset, existing = self._setup(
            endpoints=[
                _make_endpoint("users", read_param_values=[]),
            ],
            collections=[
                {"name": "users", "fields": ["name"]},
                {"name": "extra_collection", "fields": ["foo"]},
            ],
        )
        warnings = _restore_protected_structure(connection_config, dataset, existing)
        assert len(warnings) == 1
        assert warnings[0].collection == "extra_collection"
        assert "Removed" in warnings[0].message
        # The extra collection should have been removed
        assert {col.name for col in dataset.collections} == {"users"}

    def test_removed_collection_restored_with_warning(self):
        existing = _make_existing_dataset(
            collections=[
                {"name": "users", "fields": ["name"]},
                {"name": "orders", "fields": ["order_id"]},
            ]
        )
        connection_config, dataset, _ = self._setup(
            endpoints=[
                _make_endpoint("users", read_param_values=[]),
                _make_endpoint("orders", read_param_values=[]),
            ],
            collections=[
                {"name": "users", "fields": ["name"]},
            ],
        )
        warnings = _restore_protected_structure(connection_config, dataset, existing)
        assert len(warnings) == 1
        assert warnings[0].collection == "orders"
        assert "Restored" in warnings[0].message
        assert {col.name for col in dataset.collections} == {"users", "orders"}

    def test_removed_collection_no_existing_emits_warning(self):
        """Fix 4: when a collection is removed on first creation, emit a warning."""
        connection_config, dataset, _ = self._setup(
            endpoints=[
                _make_endpoint("users", read_param_values=[]),
                _make_endpoint("orders", read_param_values=[]),
            ],
            collections=[
                {"name": "users", "fields": ["name"]},
            ],
            existing_dataset=None,
        )
        warnings = _restore_protected_structure(connection_config, dataset, None)
        assert len(warnings) == 1
        assert warnings[0].collection == "orders"
        assert "missing" in warnings[0].message
        assert "could not be restored" in warnings[0].message

    def test_deleted_referenced_field_restored_with_warning(self):
        existing = _make_existing_dataset(
            collections=[
                {"name": "users", "fields": ["user_id", "name", "email"]},
            ]
        )
        connection_config, dataset, _ = self._setup(
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
        warnings = _restore_protected_structure(connection_config, dataset, existing)
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
        connection_config, dataset, existing = self._setup(
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
        warnings = _restore_protected_structure(connection_config, dataset, existing)
        assert warnings == []

    def test_adding_field_allowed_no_warning(self):
        connection_config, dataset, existing = self._setup(
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
        warnings = _restore_protected_structure(connection_config, dataset, existing)
        assert warnings == []

    def test_removing_non_referenced_field_allowed_no_warning(self):
        connection_config, dataset, existing = self._setup(
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
        warnings = _restore_protected_structure(connection_config, dataset, existing)
        assert warnings == []

    def test_delete_referenced_field_restored_with_warning(self):
        existing = _make_existing_dataset(
            collections=[
                {"name": "users", "fields": ["user_id", "name"]},
            ]
        )
        connection_config, dataset, _ = self._setup(
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
        warnings = _restore_protected_structure(connection_config, dataset, existing)
        assert len(warnings) == 1
        assert warnings[0].collection == "users"
        assert warnings[0].field == "user_id"

    def test_nested_referenced_field_restored(self):
        """Nested dot-path references (e.g. address.street) are restored correctly."""
        existing = _make_existing_dataset(
            collections=[
                {
                    "name": "users",
                    "fields": [
                        {"name": "address", "fields": ["street", "city"]},
                    ],
                },
            ]
        )
        # Reference uses dot-path "address.street"
        endpoint = _make_endpoint(
            "users",
            read_param_values=[
                {
                    "name": "street",
                    "references": [
                        {
                            "dataset": "<instance_fides_key>",
                            "field": "users.address.street",
                            "direction": "from",
                        }
                    ],
                },
            ],
        )
        config_dict = _make_saas_config_dict([endpoint])
        connection_config = _make_connection_config(config_dict)
        # Incoming dataset has address but street is missing
        dataset = _make_dataset(
            "test_connector",
            [
                {
                    "name": "users",
                    "fields": [
                        {"name": "address", "fields": ["city"]},
                    ],
                },
            ],
        )
        warnings = _restore_protected_structure(connection_config, dataset, existing)
        assert len(warnings) == 1
        assert warnings[0].field == "address.street"
        # Verify the field was actually restored
        users_col = next(c for c in dataset.collections if c.name == "users")
        address_field = next(f for f in users_col.fields if f.name == "address")
        assert {f.name for f in address_field.fields} == {"street", "city"}


class TestRestoreImmutableFields:
    def test_unchanged_metadata_no_warnings(self):
        existing = _make_existing_dataset()
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
            name="Test Connector Dataset",
            description="Original description",
        )
        warnings = _restore_immutable_fields(dataset, existing)
        assert warnings == []

    def test_changed_name_restored_with_warning(self):
        existing = _make_existing_dataset()
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
            name="Changed Name",
            description="Original description",
        )
        warnings = _restore_immutable_fields(dataset, existing)
        assert len(warnings) == 1
        assert warnings[0].collection is None
        assert warnings[0].field == "name"
        assert "'name'" in warnings[0].message
        assert dataset.name == "Test Connector Dataset"

    def test_changed_description_restored_with_warning(self):
        existing = _make_existing_dataset()
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
            name="Test Connector Dataset",
            description="Changed description",
        )
        warnings = _restore_immutable_fields(dataset, existing)
        assert len(warnings) == 1
        assert "'description'" in warnings[0].message
        assert dataset.description == "Original description"

    def test_multiple_fields_changed_multiple_warnings(self):
        existing = _make_existing_dataset()
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
            name="Changed Name",
            description="Changed description",
        )
        warnings = _restore_immutable_fields(dataset, existing)
        assert len(warnings) == 2
        assert dataset.name == "Test Connector Dataset"
        assert dataset.description == "Original description"

    def test_new_dataset_skips_immutable_check(self):
        dataset = _make_dataset(
            "test_connector",
            [{"name": "users", "fields": ["name"]}],
        )
        warnings = _restore_immutable_fields(dataset, None)
        assert warnings == []
