import logging
from datetime import datetime, timedelta
from typing import Set, Optional, Awaitable

from pydantic import ValidationError
from sqlalchemy.orm import Session

from fidesops import common_exceptions
from fidesops.core.config import config
from fidesops.db.session import get_db_session
from fidesops.common_exceptions import PrivacyRequestPaused, ClientUnsuccessfulException
from fidesops.graph.graph import DatasetGraph
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.models.policy import (
    ActionType,
    WebhookTypes,
    PolicyPreWebhook,
    PolicyPostWebhook,
)
from fidesops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fidesops.service.storage.storage_uploader_service import upload
from fidesops.task.filter_results import filter_data_categories
from fidesops.task.graph_task import (
    run_access_request,
    run_erasure,
    get_cached_data_for_erasures,
)
from fidesops.tasks.scheduled.scheduler import scheduler
from fidesops.util.async_util import run_async
from fidesops.util.cache import FidesopsRedis

logger = logging.getLogger(__name__)


class PrivacyRequestRunner:
    """The class responsible for dispatching PrivacyRequests into the execution layer"""

    def __init__(
        self,
        cache: FidesopsRedis,
        privacy_request: PrivacyRequest,
    ):
        self.cache = cache
        self.privacy_request = privacy_request

    @staticmethod
    def run_webhooks_and_report_status(
        db: Session,
        privacy_request: PrivacyRequest,
        webhook_cls: WebhookTypes,
        after_webhook_id: str = None,
    ) -> bool:
        """
        Runs a series of webhooks either pre- or post- privacy request execution, if any are configured.
        Updates privacy request status if execution is paused/errored.
        Returns True if execution should proceed.
        """
        webhooks = db.query(webhook_cls).filter_by(policy_id=privacy_request.policy.id)

        if after_webhook_id:
            # Only run webhooks configured to run after this Pre-Execution webhook
            pre_webhook = PolicyPreWebhook.get(db=db, id=after_webhook_id)
            webhooks = webhooks.filter(
                webhook_cls.order > pre_webhook.order,
            )

        for webhook in webhooks.order_by(webhook_cls.order):
            try:
                privacy_request.trigger_policy_webhook(webhook)
            except PrivacyRequestPaused:
                logging.info(
                    f"Pausing execution of privacy request {privacy_request.id}. Halt instruction received from webhook {webhook.key}."
                )
                privacy_request.update(
                    db=db, data={"status": PrivacyRequestStatus.paused}
                )
                initiate_paused_privacy_request_followup(privacy_request)
                return False
            except ClientUnsuccessfulException as exc:
                logging.error(
                    f"Privacy Request '{privacy_request.id}' exited after response from webhook '{webhook.key}': {exc.args[0]}."
                )
                privacy_request.error_processing(db)
                return False
            except ValidationError:
                logging.error(
                    f"Privacy Request '{privacy_request.id}' errored due to response validation error from webhook '{webhook.key}'."
                )
                privacy_request.error_processing(db)
                return False

        return True

    def submit(
        self, from_webhook: Optional[PolicyPreWebhook] = None
    ) -> Awaitable[None]:
        """Run this privacy request in a separate thread."""
        from_webhook_id = from_webhook.id if from_webhook else None
        return run_async(self.run, self.privacy_request.id, from_webhook_id)

    def run(
        self, privacy_request_id: str, from_webhook_id: Optional[str] = None
    ) -> None:
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
            privacy_request.start_processing(session)

            # Run pre-execution webhooks
            proceed = self.run_webhooks_and_report_status(
                session,
                privacy_request=privacy_request,
                webhook_cls=PolicyPreWebhook,
                after_webhook_id=from_webhook_id,
            )
            if not proceed:
                session.close()
                return

            policy = privacy_request.policy
            try:
                policy.rules[0]
            except IndexError:
                raise common_exceptions.MisconfiguredPolicyException(
                    f"Policy with key {policy.key} must contain at least one Rule."
                )

            try:
                datasets = DatasetConfig.all(db=session)
                dataset_graphs = [
                    dataset_config.get_graph() for dataset_config in datasets
                ]
                dataset_graph = DatasetGraph(*dataset_graphs)
                identity_data = privacy_request.get_cached_identity_data()
                connection_configs = ConnectionConfig.all(db=session)

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
                        access_result,
                        target_categories,
                        dataset_graph.data_category_field_mapping,
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
                        access_request_data=get_cached_data_for_erasures(
                            privacy_request.id
                        ),
                    )

            except BaseException as exc:  # pylint: disable=broad-except
                privacy_request.status = PrivacyRequestStatus.error
                # If dev mode, log traceback
                if config.dev_mode:
                    logging.error(exc, exc_info=True)
                else:
                    logging.error(exc)

            # Run post-execution webhooks
            proceed = self.run_webhooks_and_report_status(
                db=session,
                privacy_request=privacy_request,
                webhook_cls=PolicyPostWebhook,
            )
            if not proceed:
                session.close()
                return

            privacy_request.finished_processing_at = datetime.utcnow()
            if privacy_request.status != PrivacyRequestStatus.error:
                privacy_request.status = PrivacyRequestStatus.complete
            privacy_request.save(db=session)
            logging.info(f"Privacy request {privacy_request.id} run completed.")
            session.close()

    def dry_run(self, privacy_request: PrivacyRequest) -> None:
        """Pretend to dispatch privacy_request into the execution layer, return the query plan"""


def initiate_paused_privacy_request_followup(privacy_request: PrivacyRequest) -> None:
    """Initiates scheduler to expire privacy request when the redis cache expires"""
    scheduler.add_job(
        func=mark_paused_privacy_request_as_expired,
        kwargs={"privacy_request_id": privacy_request.id},
        id=privacy_request.id,
        replace_existing=True,
        trigger="date",
        run_date=(datetime.now() + timedelta(seconds=config.redis.DEFAULT_TTL_SECONDS)),
    )


def mark_paused_privacy_request_as_expired(privacy_request_id: str) -> None:
    """Mark "paused" PrivacyRequest as "errored" after its associated identity data in the redis cache has expired."""
    SessionLocal = get_db_session()
    db = SessionLocal()
    privacy_request = PrivacyRequest.get(db=db, id=privacy_request_id)
    if not privacy_request:
        logger.info(
            f"Attempted to mark as expired. No privacy request with id'{privacy_request_id}' found."
        )
        db.close()
        return
    if privacy_request.status == PrivacyRequestStatus.paused:
        logger.error(
            f"Privacy request '{privacy_request.id}' has expired. Please resubmit information."
        )
        privacy_request.error_processing(db=db)
    db.close()
