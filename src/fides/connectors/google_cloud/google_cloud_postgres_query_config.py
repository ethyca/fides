from fides.connectors.query_config import (
    QueryStringWithoutTuplesOverrideQueryConfig,
)


class GoogleCloudSQLPostgresQueryConfig(QueryStringWithoutTuplesOverrideQueryConfig):
    """Generates SQL in Google Cloud SQL for Postgres' custom dialect."""
