from typing import Optional

from fides.api.schemas.base_class import FidesSchema


class BigQueryNamespaceMeta(FidesSchema):
    """
    Represents the namespace structure for BigQuery queries.

    Attributes:
        project_id (Optional[str]): The ID of the Google Cloud project.
            This is optional as queries within the same project may omit it.
        dataset_id (str): The ID of the BigQuery dataset. This is required
            for all BigQuery queries to specify the dataset being queried.
    """

    project_id: Optional[str] = None
    dataset_id: str
