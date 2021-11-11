import logging
from datetime import datetime
from typing import Set

from sqlalchemy.orm import Session

from fidesops import common_exceptions
from fidesops.graph.graph import DatasetGraph
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.models.policy import ActionType
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.service.storage.storage_uploader_service import upload
from fidesops.task.graph_task import (
    run_access_request,
    filter_data_categories,
    run_erasure,
)
from fidesops.util.cache import FidesopsRedis

logging.basicConfig(level=logging.INFO)


class PrivacyRequestRunner:
    """The class responsible for dispatching PrivacyRequests into the execution layer"""

    def __init__(
        self,
        cache: FidesopsRedis,
        db: Session,
        privacy_request: PrivacyRequest,
    ):
        self.cache = cache
        self.db = db
        self.privacy_request = privacy_request

    def run(self) -> None:
        # pylint: disable=too-many-locals
        """
        Dispatch a privacy_request into the execution layer by:
            1. Generate a graph from all the currently configured datasets
            2. Take the provided identity data
            3. Start the access request / erasure request execution
            4. When finished, upload the results to the configured storage destination if applicable
        """

        logging.info(f"Dispatching privacy request {self.privacy_request.id}")
        self.start_processing(db=self.db)

        datasets = DatasetConfig.all(db=self.db)
        dataset_graphs = [dataset_config.get_graph() for dataset_config in datasets]
        dataset_graph = DatasetGraph(*dataset_graphs)
        identity_data = self.privacy_request.get_cached_identity_data()
        connection_configs = ConnectionConfig.all(db=self.db)
        policy = self.privacy_request.policy

        try:
            policy.rules[0]
        except IndexError:
            raise common_exceptions.MisconfiguredPolicyException(
                f"Policy with key {policy.key} must contain at least one Rule."
            )

        try:
            access_result = run_access_request(
                privacy_request=self.privacy_request,
                policy=policy,
                graph=dataset_graph,
                connection_configs=connection_configs,
                identity=identity_data,
            )
            if not access_result:
                logging.info(
                    f"No results returned for access request {self.privacy_request.id}"
                )

            # Once the access request is complete, process the data uploads
            for rule in policy.get_rules_for_action(action_type=ActionType.access):
                if not rule.storage_destination:
                    logging.error(
                        f"No storage destination configured on rule {rule.key}"
                    )
                    raise common_exceptions.RuleValidationError(
                        f"No storage destination configured on rule {rule.key}"
                    )
                target_categories: Set[str] = {
                    target.data_category for target in rule.targets
                }
                filtered_results = filter_data_categories(
                    access_result, target_categories, dataset_graph
                )
                logging.info(
                    f"Starting access request upload for rule {rule.key} for privacy request {self.privacy_request.id}"
                )
                try:
                    upload(
                        db=self.db,
                        request_id=self.privacy_request.id,
                        data=filtered_results,
                        storage_key=rule.storage_destination.key,
                    )
                except common_exceptions.StorageUploadError as exc:
                    logging.error(exc)
                    logging.error(
                        f"Error uploading subject access data for rule {rule.key} on policy {policy.key} and privacy request {self.privacy_request.id}"
                    )

            if policy.get_rules_for_action(action_type=ActionType.erasure):
                # We only need to run the erasure once until masking strategies are handled
                run_erasure(
                    privacy_request=self.privacy_request,
                    policy=policy,
                    graph=dataset_graph,
                    connection_configs=connection_configs,
                    identity=identity_data,
                    access_request_data=access_result,
                )

        except BaseException as exc:
            logging.debug(exc)
            raise

        self.privacy_request.finished_processing_at = datetime.utcnow()
        self.privacy_request.save(db=self.db)

    def dry_run(self, privacy_request: PrivacyRequest) -> None:
        """Pretend to dispatch privacy_request into the execution layer, return the query plan"""

    def start_processing(self, db: Session) -> None:
        """Dispatches this PrivacyRequest throughout the Fidesops System"""
        if self.privacy_request.started_processing_at is None:
            self.privacy_request.started_processing_at = datetime.utcnow()
            self.privacy_request.save(db=db)

    # TODO: This may get run in a different execution environment, we shouldn't pass
    # in the DB session
    def finish_processing(self, db: Session) -> None:
        """Called at the end of a successful PrivacyRequest execution"""
        self.privacy_request.finished_processing_at = datetime.utcnow()
        self.privacy_request.save(db=db)
        # 6. Upload results to storage specified in the Policy
        upload(
            db=db,
            request_id=self.privacy_request.id,
            data=self.privacy_request.get_results(),
            storage_key=self.privacy_request.policy.storage_destination.key,
        )
