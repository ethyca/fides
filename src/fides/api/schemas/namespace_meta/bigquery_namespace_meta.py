from typing import Literal, Set, Tuple

from fides.api.schemas.connection_configuration import secrets_schemas
from fides.api.schemas.namespace_meta.namespace_meta import NamespaceMeta


class BigQueryNamespaceMeta(NamespaceMeta):
    """
    Represents the namespace structure for BigQuery queries.

    Attributes:
        project_id (str): The ID of the Google Cloud project.
        dataset_id (str): The ID of the BigQuery dataset.
    """

    connection_type: Literal["bigquery"] = "bigquery"
    project_id: str
    dataset_id: str

    @classmethod
    def get_fallback_secret_fields(cls) -> Set[Tuple]:
        """
        The required connection config secrets when namespace metadata is missing.
        For BigQuery, dataset must be provided in secrets if dataset_id is not in namespace metadata.
        """
        schema = secrets_schemas["bigquery"]
        return {("dataset", schema.model_fields["dataset"].title)}
