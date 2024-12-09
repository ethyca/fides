from loguru import logger

from fides.api.models.sql_models import Dataset
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.service.connectors.datahub_connector import DatahubConnector
from fides.api.tasks import DatabaseTask, celery_app


@celery_app.task(base=DatabaseTask, bind=True)
def sync_fides_dataset_with_datahub(
    self: DatabaseTask, dataset_id: str, connection_config_id: str
):
    with self.get_new_session() as session:
        dataset = Dataset.get_by(db=session, field="id", value=dataset_id)
        if not dataset:
            logger.warning(
                "Dataset with id {} not found. Skipping sync with Datahub", dataset_id
            )
            return

        connection_config = session.query(ConnectionConfig).get(connection_config_id)
        if not connection_config:
            logger.warning(
                "ConnectionConfig with id {} not found. Skipping sync with Datahub",
                connection_config_id,
            )
            return

    datahub_connector = DatahubConnector(connection_config)
    datahub_connector.sync_dataset(dataset)
