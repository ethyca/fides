from typing import Literal

from fides.api.models.connectionconfig import ConnectionType
from fides.api.schemas.namespace_meta.namespace_meta import NamespaceMeta


class BigQueryNamespaceMeta(NamespaceMeta):
    """
    Represents the namespace structure for BigQuery queries.

    Attributes:
        project_id (str): The ID of the Google Cloud project.
        dataset_id (str): The ID of the BigQuery dataset.
    """

    connection_type: Literal[ConnectionType.bigquery] = ConnectionType.bigquery
    project_id: str
    dataset_id: str
