import logging
from datetime import datetime
from typing import Set, Optional, Awaitable

from pydantic import ValidationError
from sqlalchemy.orm import Session

from fidesops import common_exceptions
from fidesops.db.session import get_db_session
from fidesops.common_exceptions import PrivacyRequestPaused, ClientUnsuccessfulException
from fidesops.graph.graph import DatasetGraph
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.models.policy import (
    ActionType,
    WebhookTypes,
)
from fidesops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fidesops.service.storage.storage_uploader_service import upload
from fidesops.task.graph_task import (
    run_access_request,
    filter_data_categories,
    run_erasure,
)
from fidesops.util.async_util import run_async
from fidesops.util.cache import FidesopsRedis


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

    def run_webhooks(
        self, webhook_cls: WebhookTypes, after_webhook: Optional[WebhookTypes] = None
    ) -> bool:
        """
        Runs a series of webhooks either pre- or post- privacy request execution.
        Updates privacy request status if execution is paused/errored.
        Returns True if execution should proceed.
        """
        webhooks = self.db.query(webhook_cls).filter_by(
            policy_id=self.privacy_request.policy.id
        )

        if after_webhook:
            # Only run webhooks configured to run after this webhook
            webhooks = webhooks.filter(webhook_cls.order > after_webhook.order)

        for webhook in webhooks.order_by(webhook_cls.order):
            try:
                self.privacy_request.trigger_policy_webhook(webhook)
            except PrivacyRequestPaused:
                logging.info(
                    f"Pausing execution of privacy request {self.privacy_request.id}. Halt instruction received from webhook {webhook.key}."
                )
                self.privacy_request.update(
                    db=self.db, data={"status": PrivacyRequestStatus.paused}
                )
                return False
            except ClientUnsuccessfulException as exc:
                logging.error(
                    f"Privacy Request exited after response from webhook '{webhook.key}': {exc.args[0]}."
                )
                self.privacy_request.update(
                    db=self.db,
                    data={
                        "status": PrivacyRequestStatus.error,
                        "finished_processing_at": datetime.utcnow(),
                    },
                )
                return False
            except ValidationError:
                logging.error(
                    f"Privacy Request {self.privacy_request.id} errored due to response validation error from webhook '{webhook.key}'."
                )
                self.privacy_request.update(
                    db=self.db,
                    data={
                        "status": PrivacyRequestStatus.error,
                        "finished_processing_at": datetime.utcnow(),
                    },
                )
                return False

        return True

    def submit(self) -> Awaitable[None]:
        """Run this privacy request in a separate thread."""
        return run_async(self.run, self.privacy_request.id)

    def run(self, privacy_request_id: str) -> None:
        # pylint: disable=too-many-locals
        """
        Dispatch a privacy_request into the execution layer by:
            1. Generate a graph from all the currently configured datasets
            2. Take the provided identity data
            3. Start the access request / erasure request execution
            4. When finished, upload the results to the configured storage destination if applicable
        """
        SessionLocal = get_db_session()
        with SessionLocal() as session:

            privacy_request = PrivacyRequest.get(db=session, id=privacy_request_id)
            logging.info(f"Dispatching privacy request {privacy_request.id}")
            self.start_processing(session, privacy_request)

            datasets = DatasetConfig.all(db=session)
            dataset_graphs = [dataset_config.get_graph() for dataset_config in datasets]
            dataset_graph = DatasetGraph(*dataset_graphs)
            identity_data = privacy_request.get_cached_identity_data()
            connection_configs = ConnectionConfig.all(db=session)
            policy = privacy_request.policy
            try:
                policy.rules[0]
            except IndexError:
                raise common_exceptions.MisconfiguredPolicyException(
                    f"Policy with key {policy.key} must contain at least one Rule."
                )

            try:
                access_result = run_access_request(
                    privacy_request=privacy_request,
                    policy=policy,
                    graph=dataset_graph,
                    connection_configs=connection_configs,
                    identity=identity_data,
                )
                if not access_result:
                    logging.info(
                        f"No results returned for access request {privacy_request.id}"
                    )

                # Once the access request is complete, process the data uploads
                for rule in policy.get_rules_for_action(action_type=ActionType.access):
                    if not rule.storage_destination:
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
                        f"Starting access request upload for rule {rule.key} for privacy request {privacy_request.id}"
                    )
                    try:
                        upload(
                            db=session,
                            request_id=privacy_request.id,
                            data=filtered_results,
                            storage_key=rule.storage_destination.key,
                        )
                    except common_exceptions.StorageUploadError as exc:
                        logging.error(
                            f"Error uploading subject access data for rule {rule.key} on policy {policy.key} and privacy request {privacy_request.id} : {exc}"
                        )
                        privacy_request.status = PrivacyRequestStatus.error

                if policy.get_rules_for_action(action_type=ActionType.erasure):
                    # We only need to run the erasure once until masking strategies are handled
                    run_erasure(
                        privacy_request=privacy_request,
                        policy=policy,
                        graph=dataset_graph,
                        connection_configs=connection_configs,
                        identity=identity_data,
                        access_request_data=access_result,
                    )

            except BaseException as exc:  # pylint: disable=broad-except
                logging.error(exc)
                privacy_request.status = PrivacyRequestStatus.error

            privacy_request.finished_processing_at = datetime.utcnow()
            if privacy_request.status != PrivacyRequestStatus.error:
                privacy_request.status = PrivacyRequestStatus.complete
            privacy_request.save(db=session)
            logging.info(f"Privacy request {privacy_request.id} run completed.")
            session.close()

    def dry_run(self, privacy_request: PrivacyRequest) -> None:
        """Pretend to dispatch privacy_request into the execution layer, return the query plan"""

    def start_processing(self, db: Session, privacy_request: PrivacyRequest) -> None:
        """Dispatches this PrivacyRequest throughout the Fidesops System"""
        if privacy_request.started_processing_at is None:
            privacy_request.started_processing_at = datetime.utcnow()
            privacy_request.save(db=db)

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
