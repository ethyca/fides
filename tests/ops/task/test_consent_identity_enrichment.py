from typing import Dict, List
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from fideslang.validation import FidesKey

from fides.api.graph.config import (
    Collection,
    GraphDataset,
    ScalarField,
)
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.schemas.policy import ActionType
from fides.api.service.connectors.query_configs.query_config import SQLQueryConfig
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.api.task.consent_identity_enrichment import enrich_identities_for_consent
from fides.api.task.graph_task import build_consent_identity_enrichment_graph
from fides.config import CONFIG


@pytest.fixture()
def enable_identity_enrichment():
    CONFIG.consent.identity_enrichment = True
    yield
    CONFIG.consent.identity_enrichment = False


def _make_users_collection(
    *,
    name: str = "users",
    identity_fields: Dict[str, str] | None = None,
) -> Collection:
    if identity_fields is None:
        identity_fields = {"email": "email", "external_id": "external_id"}
    fields = [ScalarField(name="id", primary_key=True)]
    for field_name, identity_type in identity_fields.items():
        fields.append(ScalarField(name=field_name, identity=identity_type))
    return Collection(name=name, fields=fields)


def _make_graph_dataset(
    name: str,
    connection_key: str,
    collections: List[Collection] | None = None,
) -> GraphDataset:
    if collections is None:
        collections = [_make_users_collection()]
    return GraphDataset(
        name=name,
        collections=collections,
        connection_key=FidesKey(connection_key),
    )


def _make_mock_dataset_config(
    *,
    connection_type: ConnectionType = ConnectionType.postgres,
    enabled_actions: list[ActionType] | None = None,
    disabled: bool = False,
    connection_key: str = "test_postgres",
    dataset_name: str = "test_db",
    identity_fields: Dict[str, str] | None = None,
) -> MagicMock:
    mock_config = MagicMock(spec=DatasetConfig)
    mock_connection = MagicMock(spec=ConnectionConfig)
    mock_connection.connection_type = connection_type
    mock_connection.enabled_actions = enabled_actions
    mock_connection.disabled = disabled
    mock_connection.key = connection_key

    if connection_type == ConnectionType.saas:
        mock_saas = MagicMock()
        mock_saas.supported_actions = [ActionType.consent]
        mock_connection.get_saas_config.return_value = mock_saas
    else:
        mock_connection.get_saas_config.return_value = None

    mock_config.connection_config = mock_connection

    collections = [_make_users_collection(identity_fields=identity_fields)]
    graph = _make_graph_dataset(dataset_name, connection_key, collections)
    mock_config.get_graph.return_value = graph
    mock_config.get_dataset_with_stubbed_collection.return_value = graph

    return mock_config


def _make_sql_connector_mock(
    rows: List[Dict] | None = None,
) -> MagicMock:
    """
    Create a mock SQLConnector that returns the given rows from query execution.

    Mocks the connector's query_config to use a real SQLQueryConfig (which
    generates correct SQL) with the enrichment node, then mocks the engine's
    execute to return the expected rows.
    """
    mock_connector = create_autospec(SQLConnector, instance=True)

    mock_result = MagicMock()
    if rows:
        col_mocks = []
        for col_name in rows[0].keys():
            col_mock = MagicMock()
            col_mock.name = col_name
            col_mocks.append(col_mock)
        mock_result.cursor.description = col_mocks
        mock_result.__iter__ = lambda self: iter([tuple(row.values()) for row in rows])
    else:
        mock_result.cursor.description = []
        mock_result.__iter__ = lambda self: iter([])

    mock_connection = MagicMock()
    mock_connection.execute.return_value = mock_result

    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_connection)
    mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    mock_connector.client.return_value = mock_engine

    def _query_config(node):
        return SQLQueryConfig(node)

    mock_connector.query_config = _query_config
    mock_connector.cursor_result_to_rows = SQLConnector.cursor_result_to_rows

    return mock_connector


def _make_enrichment_setup(
    *,
    enabled_actions: list[ActionType] | None = None,
    connection_type: ConnectionType = ConnectionType.postgres,
    connection_key: str = "pg_consent",
    identity_fields: Dict[str, str] | None = None,
) -> tuple[list, list, MagicMock]:
    if enabled_actions is None:
        enabled_actions = [ActionType.consent]

    dataset_config = _make_mock_dataset_config(
        connection_type=connection_type,
        enabled_actions=enabled_actions,
        connection_key=connection_key,
        dataset_name="identity_db",
        identity_fields=identity_fields,
    )

    mock_conn_config = MagicMock(spec=ConnectionConfig)
    mock_conn_config.key = connection_key
    mock_conn_config.connection_type = connection_type
    mock_conn_config.disabled = False
    mock_conn_config.enabled_actions = enabled_actions
    mock_conn_config.datasets = []

    mock_privacy_request = MagicMock()

    return [dataset_config], [mock_conn_config], mock_privacy_request


class TestBuildConsentIdentityEnrichmentGraph:
    def test_includes_postgres_with_consent_enabled(self):
        dataset_config = _make_mock_dataset_config(
            connection_type=ConnectionType.postgres,
            enabled_actions=[ActionType.consent],
        )
        graph = build_consent_identity_enrichment_graph([dataset_config])
        assert len(graph.nodes) > 0
        collection_names = [addr.collection for addr in graph.nodes.keys()]
        assert "users" in collection_names

    def test_excludes_saas_connectors(self):
        dataset_config = _make_mock_dataset_config(
            connection_type=ConnectionType.saas,
            enabled_actions=[ActionType.consent],
            connection_key="saas_connector",
        )
        graph = build_consent_identity_enrichment_graph([dataset_config])
        assert len(graph.nodes) == 0

    def test_excludes_disabled_connections(self):
        dataset_config = _make_mock_dataset_config(
            enabled_actions=[ActionType.consent],
            disabled=True,
        )
        graph = build_consent_identity_enrichment_graph([dataset_config])
        assert len(graph.nodes) == 0

    def test_excludes_enabled_actions_none(self):
        dataset_config = _make_mock_dataset_config(enabled_actions=None)
        graph = build_consent_identity_enrichment_graph([dataset_config])
        assert len(graph.nodes) == 0

    def test_excludes_no_consent_in_enabled_actions(self):
        dataset_config = _make_mock_dataset_config(
            enabled_actions=[ActionType.access, ActionType.erasure],
        )
        graph = build_consent_identity_enrichment_graph([dataset_config])
        assert len(graph.nodes) == 0

    def test_empty_datasets_list(self):
        graph = build_consent_identity_enrichment_graph([])
        assert len(graph.nodes) == 0

    def test_multiple_db_integrations_only_consent_enabled_included(self):
        consent_ds = _make_mock_dataset_config(
            enabled_actions=[ActionType.consent],
            connection_key="pg_consent",
            dataset_name="consent_db",
        )
        no_consent_ds = _make_mock_dataset_config(
            enabled_actions=[ActionType.access],
            connection_key="pg_access",
            dataset_name="access_db",
        )
        graph = build_consent_identity_enrichment_graph([consent_ds, no_consent_ds])
        dataset_names = {addr.dataset for addr in graph.nodes.keys()}
        assert "consent_db" in dataset_names
        assert "access_db" not in dataset_names

    def test_uses_full_graph_not_stubbed(self):
        dataset_config = _make_mock_dataset_config(
            enabled_actions=[ActionType.consent],
        )
        build_consent_identity_enrichment_graph([dataset_config])
        dataset_config.get_graph.assert_called_once()
        dataset_config.get_dataset_with_stubbed_collection.assert_not_called()


@pytest.mark.usefixtures("enable_identity_enrichment")
class TestEnrichIdentitiesForConsent:
    """Tests for the public enrich_identities_for_consent function.

    Mocks at the get_connector boundary (Protocol/ABC boundary to external
    infrastructure) and the DSR cache store (Redis). The connector mock
    uses a real SQLQueryConfig for query generation.
    """

    @pytest.fixture(autouse=True)
    def _store_db(self, db):
        self.db = db

    @pytest.fixture(autouse=True)
    def mock_cache_store(self):
        with patch(
            "fides.api.task.consent_identity_enrichment.get_dsr_cache_store"
        ) as mock_store:
            mock_store.return_value = MagicMock()
            yield mock_store

    @patch("fides.api.task.consent_identity_enrichment.SQLConnector.get_namespace_meta")
    @patch("fides.api.task.consent_identity_enrichment.get_connector")
    def test_enriches_email_from_external_id(
        self, mock_get_connector, mock_namespace_meta
    ):
        mock_namespace_meta.return_value = None
        mock_get_connector.return_value = _make_sql_connector_mock(
            [{"email": "found@test.com", "external_id": "ext_123"}]
        )
        datasets, configs, pr = _make_enrichment_setup()
        result = enrich_identities_for_consent(
            datasets, configs, {"external_id": "ext_123"}, pr, self.db
        )
        assert result["external_id"] == "ext_123"
        assert result["email"] == "found@test.com"

    @patch("fides.api.task.consent_identity_enrichment.SQLConnector.get_namespace_meta")
    @patch("fides.api.task.consent_identity_enrichment.get_connector")
    def test_enriches_external_id_from_email(
        self, mock_get_connector, mock_namespace_meta
    ):
        mock_namespace_meta.return_value = None
        mock_get_connector.return_value = _make_sql_connector_mock(
            [{"email": "user@test.com", "external_id": "ext_456"}]
        )
        datasets, configs, pr = _make_enrichment_setup()
        result = enrich_identities_for_consent(
            datasets, configs, {"email": "user@test.com"}, pr, self.db
        )
        assert result["email"] == "user@test.com"
        assert result["external_id"] == "ext_456"

    @patch("fides.api.task.consent_identity_enrichment.SQLConnector.get_namespace_meta")
    @patch("fides.api.task.consent_identity_enrichment.get_connector")
    def test_no_new_identities_when_all_present(
        self, mock_get_connector, mock_namespace_meta
    ):
        mock_namespace_meta.return_value = None
        mock_get_connector.return_value = _make_sql_connector_mock(
            [{"email": "x@y.com", "external_id": "abc"}]
        )
        datasets, configs, pr = _make_enrichment_setup()
        identity = {"email": "x@y.com", "external_id": "abc"}
        result = enrich_identities_for_consent(datasets, configs, identity, pr, self.db)
        assert result == identity

    def test_no_enrichment_when_no_consent_db_integrations(self):
        dataset_config = _make_mock_dataset_config(
            enabled_actions=[ActionType.access],
        )
        pr = MagicMock()
        identity = {"external_id": "abc"}
        result = enrich_identities_for_consent(
            [dataset_config], [], identity, pr, self.db
        )
        assert result == identity

    def test_no_enrichment_when_empty_datasets(self):
        pr = MagicMock()
        identity = {"external_id": "abc"}
        result = enrich_identities_for_consent([], [], identity, pr, self.db)
        assert result == identity

    def test_saas_excluded_from_enrichment(self):
        dataset_config = _make_mock_dataset_config(
            connection_type=ConnectionType.saas,
            enabled_actions=[ActionType.consent],
            connection_key="saas_consent",
            dataset_name="saas_db",
        )
        pr = MagicMock()
        identity = {"external_id": "abc"}
        result = enrich_identities_for_consent(
            [dataset_config], [], identity, pr, self.db
        )
        assert result == identity

    @patch("fides.api.task.consent_identity_enrichment.SQLConnector.get_namespace_meta")
    @patch("fides.api.task.consent_identity_enrichment.get_connector")
    def test_graceful_fallback_on_db_error(
        self, mock_get_connector, mock_namespace_meta
    ):
        mock_namespace_meta.return_value = None
        mock_connector = create_autospec(SQLConnector, instance=True)
        mock_connector.client.side_effect = Exception("Connection refused")
        mock_connector.query_config = lambda node: SQLQueryConfig(node)
        mock_get_connector.return_value = mock_connector
        datasets, configs, pr = _make_enrichment_setup()
        identity = {"external_id": "ext_123"}
        result = enrich_identities_for_consent(datasets, configs, identity, pr, self.db)
        assert result == identity

    @patch("fides.api.task.consent_identity_enrichment.SQLConnector.get_namespace_meta")
    @patch("fides.api.task.consent_identity_enrichment.get_connector")
    def test_graceful_fallback_user_not_found(
        self, mock_get_connector, mock_namespace_meta
    ):
        mock_namespace_meta.return_value = None
        mock_get_connector.return_value = _make_sql_connector_mock([])
        datasets, configs, pr = _make_enrichment_setup()
        identity = {"external_id": "ext_123"}
        result = enrich_identities_for_consent(datasets, configs, identity, pr, self.db)
        assert result == identity

    @patch("fides.api.task.consent_identity_enrichment.SQLConnector.get_namespace_meta")
    @patch("fides.api.task.consent_identity_enrichment.get_connector")
    def test_does_not_overwrite_existing_identities(
        self, mock_get_connector, mock_namespace_meta
    ):
        mock_namespace_meta.return_value = None
        mock_get_connector.return_value = _make_sql_connector_mock(
            [{"email": "different@test.com", "external_id": "ext_123"}]
        )
        datasets, configs, pr = _make_enrichment_setup()
        identity = {"email": "original@test.com", "external_id": "ext_123"}
        result = enrich_identities_for_consent(datasets, configs, identity, pr, self.db)
        assert result["email"] == "original@test.com"

    @patch("fides.api.task.consent_identity_enrichment.SQLConnector.get_namespace_meta")
    @patch("fides.api.task.consent_identity_enrichment.get_connector")
    def test_does_not_mutate_original_dict(
        self, mock_get_connector, mock_namespace_meta
    ):
        mock_namespace_meta.return_value = None
        mock_get_connector.return_value = _make_sql_connector_mock(
            [{"email": "found@test.com", "external_id": "ext_123"}]
        )
        datasets, configs, pr = _make_enrichment_setup()
        original = {"external_id": "ext_123"}
        original_copy = dict(original)
        result = enrich_identities_for_consent(datasets, configs, original, pr, self.db)
        assert original == original_copy
        assert result != original

    @patch("fides.api.task.consent_identity_enrichment.SQLConnector.get_namespace_meta")
    @patch("fides.api.task.consent_identity_enrichment.get_connector")
    def test_preserves_existing_identity_adds_missing(
        self, mock_get_connector, mock_namespace_meta
    ):
        mock_namespace_meta.return_value = None
        mock_get_connector.return_value = _make_sql_connector_mock(
            [{"email": "db@test.com", "external_id": "ext_456"}]
        )
        datasets, configs, pr = _make_enrichment_setup()
        result = enrich_identities_for_consent(
            datasets, configs, {"email": "my@test.com"}, pr, self.db
        )
        assert result["email"] == "my@test.com"
        assert result["external_id"] == "ext_456"

    @patch("fides.api.task.consent_identity_enrichment.SQLConnector.get_namespace_meta")
    @patch("fides.api.task.consent_identity_enrichment.get_connector")
    def test_enriches_multiple_missing_identities(
        self, mock_get_connector, mock_namespace_meta
    ):
        mock_namespace_meta.return_value = None
        mock_get_connector.return_value = _make_sql_connector_mock(
            [
                {
                    "email": "found@test.com",
                    "external_id": "ext_1",
                    "phone": "555-0100",
                }
            ]
        )
        datasets, configs, pr = _make_enrichment_setup(
            identity_fields={
                "email": "email",
                "external_id": "external_id",
                "phone": "phone_number",
            }
        )
        result = enrich_identities_for_consent(
            datasets, configs, {"email": "found@test.com"}, pr, self.db
        )
        assert result["email"] == "found@test.com"
        assert result["external_id"] == "ext_1"
        assert result["phone_number"] == "555-0100"

    @patch("fides.api.task.consent_identity_enrichment.SQLConnector.get_namespace_meta")
    @patch("fides.api.task.consent_identity_enrichment.get_connector")
    def test_skips_null_identity_values_in_db_row(
        self, mock_get_connector, mock_namespace_meta
    ):
        mock_namespace_meta.return_value = None
        mock_get_connector.return_value = _make_sql_connector_mock(
            [{"email": None, "external_id": "ext_123"}]
        )
        datasets, configs, pr = _make_enrichment_setup()
        result = enrich_identities_for_consent(
            datasets, configs, {"external_id": "ext_123"}, pr, self.db
        )
        assert "email" not in result

    @patch("fides.api.task.consent_identity_enrichment.SQLConnector.get_namespace_meta")
    @patch("fides.api.task.consent_identity_enrichment.get_connector")
    def test_uses_first_row_when_multiple_returned(
        self, mock_get_connector, mock_namespace_meta
    ):
        mock_namespace_meta.return_value = None
        mock_get_connector.return_value = _make_sql_connector_mock(
            [
                {"email": "first@test.com", "external_id": "ext_123"},
                {"email": "second@test.com", "external_id": "ext_123"},
            ]
        )
        datasets, configs, pr = _make_enrichment_setup()
        result = enrich_identities_for_consent(
            datasets, configs, {"external_id": "ext_123"}, pr, self.db
        )
        assert result["email"] == "first@test.com"

    def test_enabled_actions_none_excluded(self):
        dataset_config = _make_mock_dataset_config(enabled_actions=None)
        pr = MagicMock()
        result = enrich_identities_for_consent(
            [dataset_config], [], {"external_id": "abc"}, pr, self.db
        )
        assert result == {"external_id": "abc"}

    def test_seed_identity_not_in_collection_skips_lookup(self):
        datasets, configs, pr = _make_enrichment_setup(
            identity_fields={"email": "email", "external_id": "external_id"}
        )
        result = enrich_identities_for_consent(
            datasets, configs, {"phone_number": "555-0100"}, pr, self.db
        )
        assert result == {"phone_number": "555-0100"}

    @patch("fides.api.task.consent_identity_enrichment.get_connector")
    def test_non_sql_connector_skipped(self, mock_get_connector):
        mock_get_connector.return_value = MagicMock()
        datasets, configs, pr = _make_enrichment_setup()
        result = enrich_identities_for_consent(
            datasets, configs, {"external_id": "ext_123"}, pr, self.db
        )
        assert result == {"external_id": "ext_123"}
