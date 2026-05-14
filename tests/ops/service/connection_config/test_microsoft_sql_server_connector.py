import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.service.connectors import MicrosoftSQLServerConnector


def test_mssql_connector_build_uri_default(
    connection_config_mssql: ConnectionConfig, db: Session
):
    """``build_uri()`` should reflect the ``dbname`` stored in secrets."""
    connector = MicrosoftSQLServerConnector(configuration=connection_config_mssql)
    s = connection_config_mssql.secrets

    url = connector.build_uri()

    assert url.drivername == "mssql+pymssql"
    assert url.username == s["username"]
    assert url.password == s["password"]
    assert url.host == s["host"]
    assert url.database == s["dbname"]
    assert "read_only" not in url.query


def test_mssql_connector_build_uri_dbname_override(
    connection_config_mssql: ConnectionConfig, db: Session
):
    """
    When a ``dbname`` is passed, it overrides the secret's ``dbname`` without
    mutating the underlying ``ConnectionConfig``. This is what the discovery
    monitor relies on to scan each database on an instance.
    """
    connector = MicrosoftSQLServerConnector(configuration=connection_config_mssql)
    original_dbname = connection_config_mssql.secrets["dbname"]

    url = connector.build_uri(dbname="other_db")

    assert url.database == "other_db"
    assert connection_config_mssql.secrets["dbname"] == original_dbname


@pytest.mark.parametrize(
    "read_only_override, expected_query",
    [
        pytest.param(
            {"read_only_connection": True},
            {"read_only": "True"},
            id="enabled-routes-to-secondary",
        ),
        pytest.param(
            {"read_only_connection": False},
            {},
            id="disabled-omits-query-param",
        ),
        pytest.param({}, {}, id="unset-omits-query-param"),
    ],
)
def test_mssql_connector_build_uri_read_only_routing(
    connection_config_mssql: ConnectionConfig,
    db: Session,
    read_only_override: dict,
    expected_query: dict,
):
    """
    ``read_only_connection=True`` should emit ``read_only=True`` so pymssql
    sets ``ApplicationIntent=ReadOnly`` and the Always-On listener routes to
    the read-only replica.
    """
    connection_config_mssql.secrets = {
        **connection_config_mssql.secrets,
        **read_only_override,
    }
    connection_config_mssql.save(db)
    connector = MicrosoftSQLServerConnector(configuration=connection_config_mssql)

    url = connector.build_uri()

    assert dict(url.query) == expected_query
