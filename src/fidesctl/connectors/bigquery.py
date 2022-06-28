from google.api_core.exceptions import ClientError
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from fidesctl.connectors.models import BigQueryConfig, ConnectorFailureException


def get_bigquery_engine(bigquery_config: BigQueryConfig) -> Engine:
    """
    Creates the SQLAlchemy engine for connecting to a BigQuery dataset
    """
    project_id = bigquery_config.keyfile_creds.project_id
    dataset = bigquery_config.dataset
    engine = create_engine(
        f"bigquery://{project_id}/{dataset}",
        credentials_info=bigquery_config.keyfile_creds.dict(),
    )
    return engine


def validate_bigquery_engine(bigquery_config: BigQueryConfig) -> None:
    """
    Tests the BigQuery engine by calling the schema inspection

    Using the .connect() method does not produce an exception
    """
    engine = get_bigquery_engine(bigquery_config)
    inspector = inspect(engine)
    try:
        inspector.get_schema_names()
    except ClientError as error:
        raise ConnectorFailureException(error.message)
