from json import loads

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

from fides.connectors.models import BigQueryConfig, ConnectorFailureException


def get_bigquery_engine(bigquery_config: BigQueryConfig) -> Engine:
    """
    Creates the SQLAlchemy engine for connecting to a BigQuery dataset
    """
    project_id = bigquery_config.keyfile_creds.project_id
    dataset = bigquery_config.dataset
    engine = create_engine(
        f"bigquery://{project_id}/{dataset}",
        credentials_info=bigquery_config.keyfile_creds.model_dump(mode="json"),
    )
    validate_bigquery_engine(engine)
    return engine


def validate_bigquery_engine(engine: Engine) -> None:
    """
    Tests the BigQuery engine by calling the schema inspection

    Using the .connect() method does not produce an exception
    """
    from google.api_core.exceptions import ClientError

    inspector = inspect(engine)
    try:
        inspector.get_schema_names()
    except ClientError as error:
        raise ConnectorFailureException(loads(error.response.text)["error"]["message"])
