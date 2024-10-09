from fides.api.schemas.namespace_meta.namespace_meta import NamespaceMeta


class BigQueryNamespaceMeta(NamespaceMeta):
    """
    Represents the namespace structure for BigQuery queries.

    Attributes:
        project_id (str): The ID of the Google Cloud project.
        dataset_id (str): The ID of the BigQuery dataset.
    """

    project_id: str
    dataset_id: str
