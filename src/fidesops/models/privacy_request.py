# pylint: disable=R0401
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set

from enum import Enum as EnumType

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    Column,
    DateTime,
    Enum as EnumColumn,
    ForeignKey,
    String,
)

from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship, Session

from fidesops import common_exceptions
from fidesops.db.base_class import Base
from fidesops.models.client import ClientDetail
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.graph.graph import DatasetGraph
from fidesops.models.policy import Policy, ActionType
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.schemas.third_party.onetrust import (
    OneTrustSubtaskStatus,
    OneTrustSubtaskContext,
)
from fidesops.service.storage.storage_uploader_service import upload
from fidesops.util.cache import (
    get_all_cache_keys_for_privacy_request,
    get_cache,
    get_identity_cache_key,
    FidesopsRedis,
)

logging.basicConfig(level=logging.INFO)


class PrivacyRequestStatus(EnumType):
    """Enum for privacy request statuses, reflecting where they are in the Privacy Request Lifecycle"""

    in_processing = "in_processing"
    pending = "pending"
    complete = "complete"
    error = "error"


class PrivacyRequest(Base):
    """
    The DB ORM model to describe current and historic PrivacyRequests. A privacy request is a
    database record representing a data subject request's progression within the FidesOps system.
    """

    external_id = Column(String, index=True)
    # When the request was dispatched into the FideOps pipeline
    started_processing_at = Column(DateTime(timezone=True), nullable=True)
    # When the request finished or errored in the FidesOps pipeline
    finished_processing_at = Column(DateTime(timezone=True), nullable=True)
    # When the request was created at the origin
    requested_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        EnumColumn(PrivacyRequestStatus),
        index=True,
        nullable=False,
    )
    client_id = Column(
        String,
        ForeignKey(ClientDetail.id_field_path),
    )
    client = relationship(
        ClientDetail,
        backref="privacy_requests",
    )  # Which client submitted the privacy request
    origin = Column(String, nullable=True)  # The origin from the HTTP request
    policy_id = Column(
        String,
        ForeignKey(Policy.id_field_path),
    )
    policy = relationship(
        Policy,
        backref="privacy_requests",
    )

    def delete(self, db: Session) -> None:
        """
        Clean up the cached data related to this privacy request before deleting this
        object from the database
        """
        cache: FidesopsRedis = get_cache()
        all_keys = get_all_cache_keys_for_privacy_request(privacy_request_id=self.id)
        for key in all_keys:
            cache.delete(key)
        super().delete(db=db)

    def cache_identity(self, identity: PrivacyRequestIdentity) -> None:
        """Sets the identity's values at their specific locations in the FideOps app cache"""
        cache: FidesopsRedis = get_cache()
        identity_dict: Dict[str, Any] = dict(identity)
        for key, value in identity_dict.items():
            if value is not None:
                cache.set_with_autoexpire(
                    get_identity_cache_key(self.id, key),
                    value,
                )

    def get_cached_identity_data(self) -> Dict[str, Any]:
        """Retrieves any identity data pertaining to this request from the cache"""
        prefix = f"id-{self.id}-identity-*"
        cache: FidesopsRedis = get_cache()
        keys = cache.keys(prefix)
        return {key.split("-")[-1]: cache.get(key) for key in keys}

    def get_results(self) -> Dict[str, Any]:
        """Retrieves all cached identity data associated with this Privacy Request"""
        cache: FidesopsRedis = get_cache()
        result_prefix = f"{self.id}__*"
        return cache.get_encoded_objects_by_prefix(result_prefix)

    def start_processing(
        self, db: Session, onetrust_context: Optional[OneTrustSubtaskContext] = None
    ) -> None:
        """Dispatches this PrivacyRequest throughout the Fidesops System"""
        if self.started_processing_at is None:
            self.started_processing_at = datetime.utcnow()
            self.save(db=db)

    # TODO: This may get run in a different execution environment, we shouldn't pass
    # in the DB session
    def finish_processing(self, db: Session) -> None:
        """Called at the end of a successful PrivacyRequest execution"""
        self.finished_processing_at = datetime.utcnow()
        self.save(db=db)
        # 6. Upload results to storage specified in the Policy
        upload(
            db=db,
            request_id=self.id,
            data=self.get_results(),
            storage_key=self.policy.storage_destination.key,
        )

    def on_success(self) -> None:
        """A callback to be called on privacy request processing success"""
        # todo: shortcut due to circular import
        from fidesops.service.request_intake.onetrust_service import transition_status

        transition_status(OneTrustSubtaskStatus.COMPLETED, self.onetrust_context)

    def on_error(self) -> None:
        """A callback to be called on privacy request processing error"""
        # todo: shortcut due to circular import
        from fidesops.service.request_intake.onetrust_service import transition_status

        transition_status(OneTrustSubtaskStatus.FAILED, self.onetrust_context)


class PrivacyRequestRunner:
    """The class responsible for dispatching PrivacyRequests into the execution layer"""

    def __init__(
        self,
        cache: FidesopsRedis,
        db: Session,
        privacy_request: PrivacyRequest,
        onetrust_context: Optional[OneTrustSubtaskContext] = None,
    ):
        self.cache = cache
        self.db = db
        self.privacy_request = privacy_request
        self.onetrust_context = onetrust_context

    def run(self) -> None:
        # pylint: disable=too-many-locals
        """
        Dispatch a privacy_request into the execution layer by:
            1. Generate a graph from all the currently configured datasets
            2. Take the provided identity data
            3. Start the access request / erasure request execution
            4. When finished, upload the results to the configured storage destination if applicable
        """
        from fidesops.task.graph_task import (
            filter_data_categories,
            run_access_request,
            run_erasure,
        )

        logging.info(f"Dispatching privacy request {self.privacy_request.id}")
        self.privacy_request.start_processing(db=self.db)

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
            if self.onetrust_context is not None:
                self.privacy_request.on_error()
            raise
        else:
            if self.onetrust_context is not None:
                self.privacy_request.on_success()

        self.privacy_request.finished_processing_at = datetime.utcnow()
        self.privacy_request.save(db=self.db)

    def dry_run(self, privacy_request: PrivacyRequest) -> None:
        """Pretend to dispatch privacy_request into the execution layer, return the query plan"""


class ExecutionLogStatus(EnumType):
    """Enum for execution log statuses, reflecting where they are in their workflow"""

    in_processing = "in_processing"
    pending = "pending"
    complete = "complete"
    error = "error"
    retrying = "retrying"


class ExecutionLog(Base):
    """
    Stores the individual execution logs associated with a PrivacyRequest.

    Execution logs contain information about the individual queries as they progress through the workflow
    generated by the query builder.
    """

    # Name of the fides-annotated dataset, for example: my-mongo-db
    dataset_name = Column(String, index=True)
    # Name of the particular collection or table affected
    collection_name = Column(String, index=True)
    # A JSON Array describing affected fields along with their data categories and paths
    fields_affected = Column(MutableList.as_mutable(JSONB), nullable=True)
    # Contains info, warning, or error messages
    message = Column(String)
    action_type = Column(
        EnumColumn(ActionType),
        index=True,
        nullable=False,
    )
    status = Column(
        EnumColumn(ExecutionLogStatus),
        index=True,
        nullable=False,
    )

    privacy_request_id = Column(
        String,
        nullable=False,
        index=True,
    )
    # privacy_request = relationship("PrivacyRequest", foreign_keys=[privacy_request_id], primaryjoin='ExecutionLog.privacy_request_id==PrivacyRequest.id', backref=backref("execution_logs", lazy="dynamic"))
