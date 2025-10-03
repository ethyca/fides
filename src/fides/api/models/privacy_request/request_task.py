# pylint: disable=R0401, C0302

from __future__ import annotations

from enum import Enum as EnumType
from typing import TYPE_CHECKING, List, Optional, Tuple

from loguru import logger
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Query, RelationshipProperty, Session, relationship
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.db.base_class import Base, JSONTypeOverride  # type: ignore[attr-defined]
from fides.api.db.util import EnumColumn
from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
)
from fides.api.models.field_types import EncryptedLargeDataDescriptor
from fides.api.models.privacy_request.execution_log import (
    COMPLETED_EXECUTION_LOG_STATUSES,
)
from fides.api.models.worker_task import ExecutionLogStatus, WorkerTask
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.policy import ActionType
from fides.api.util.cache import (
    FidesopsRedis,
    celery_tasks_in_flight,
    get_async_task_tracking_cache_key,
    get_cache,
)
from fides.api.util.collection_util import Row
from fides.config import CONFIG

if TYPE_CHECKING:
    from fides.api.models.privacy_request.privacy_request import PrivacyRequest


class TraversalDetails(FidesSchema):
    """Schema to format saving pre-calculated traversal details on RequestTask.traversal_details"""

    dataset_connection_key: str
    incoming_edges: List[Tuple[str, str]]
    outgoing_edges: List[Tuple[str, str]]
    input_keys: List[str]
    skipped_nodes: Optional[List[Tuple[str, str]]] = None

    # TODO: remove this method once we support custom request fields in DSR graph.
    @classmethod
    def create_empty_traversal(cls, connection_key: str) -> TraversalDetails:
        """
        Creates an "empty" TraversalDetails object that only has the dataset connection key set.
        This is a bit of a hacky workaround needed to implement the Dynamic Erasure Emails feature,
        but we should no longer need it once the custom_request_fields are included in our graph
        traversal
        """
        return cls(
            dataset_connection_key=connection_key,
            incoming_edges=[],
            outgoing_edges=[],
            input_keys=[],
            skipped_nodes=[],
        )


class AsyncTaskType(EnumType):
    """
    Enum for asynchronous RequestTask types

    These tasks differ from our regular tasks in that they are not finished on the same process that they are created,
    but rather are put into a pause state and then triggered to completion by a different process

    manual: A task that is manually triggered by the user
    polling: A task that is triggered by a polling mechanism
    callback: A task that is triggered by a callback from an external system

    """

    manual = "manual"
    polling = "polling"
    callback = "callback"


# TODO: At some point we will refactor this model to store all task types in a common table that links to tables with specific task attributes.
class RequestTask(WorkerTask, Base):
    """
    An individual Task for a Privacy Request.

    When we execute a PrivacyRequest, we build a graph by combining the current datasets with the identity data
    and we save the nodes (collections) in the graph as Request Tasks.

    Currently, we build access, erasure, and consent Request Tasks.
    """

    privacy_request_id = Column(
        String,
        ForeignKey("privacyrequest.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Identifiers of this request task
    collection_address = Column(
        String, nullable=False, index=True
    )  # Of the format dataset_name:collection_name for convenience
    dataset_name = Column(String, nullable=False, index=True)
    collection_name = Column(String, nullable=False, index=True)

    upstream_tasks = Column(
        MutableList.as_mutable(JSONB)
    )  # List of collection address strings
    downstream_tasks = Column(
        MutableList.as_mutable(JSONB)
    )  # List of collection address strings
    all_descendant_tasks = Column(
        MutableList.as_mutable(JSONB)
    )  # All tasks that can be reached by the current task.  This is useful when this task fails,
    # and we can mark every single one of these as failed.

    # Raw data retrieved from an access request is stored here.  This contains all of the
    # intermediate data we retrieved, needed for downstream tasks, but hasn't been filtered
    # by data category for the end user.
    _access_data = Column(  # An encrypted JSON String - saved as a list of Rows
        "access_data",
        StringEncryptedType(
            type_in=JSONTypeOverride,
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )

    # This is the raw access data saved in erasure format (with placeholders preserved) to perform a masking request.
    # First saved on the access node, and then copied to the corresponding erasure node.
    _data_for_erasures = Column(  # An encrypted JSON String - saved as a list of rows
        "data_for_erasures",
        StringEncryptedType(
            type_in=JSONTypeOverride,
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )

    # Use descriptors for automatic external storage handling
    access_data = EncryptedLargeDataDescriptor(
        field_name="access_data", empty_default=[]
    )

    data_for_erasures = EncryptedLargeDataDescriptor(
        field_name="data_for_erasures", empty_default=[]
    )

    # Written after an erasure is completed
    rows_masked = Column(Integer)
    # Written after a consent request is completed - not all consent
    # connectors will end up sending a request
    consent_sent = Column(Boolean)

    # For async tasks awaiting callback
    callback_succeeded = Column(Boolean)
    # to recognize Polling async task
    async_type = Column(
        EnumColumn(AsyncTaskType, native_enum=True),
        nullable=True,
    )

    # Stores a serialized collection that can be transformed back into a Collection to help
    # execute the current task
    collection = Column(MutableDict.as_mutable(JSONB))
    # Stores key details from traversal.traverse in the format of TraversalDetails
    traversal_details = Column(MutableDict.as_mutable(JSONB))

    privacy_request = relationship(
        "PrivacyRequest",
        back_populates="request_tasks",
        uselist=False,
    )

    # Stores the sub-requests data for async polling tasks
    sub_requests: "RelationshipProperty[List[RequestTaskSubRequest]]" = relationship(
        "RequestTaskSubRequest",
        back_populates="request_task",
        cascade="all, delete-orphan",
        order_by="RequestTaskSubRequest.created_at",
    )

    @property
    def request_task_address(self) -> CollectionAddress:
        """Convert the collection_address into Collection Address format"""
        return CollectionAddress.from_string(self.collection_address)

    @property
    def is_root_task(self) -> bool:
        """Convenience helper for asserting whether the task is a root task"""
        return self.request_task_address == ROOT_COLLECTION_ADDRESS

    @property
    def is_terminator_task(self) -> bool:
        """Convenience helper for asserting whether the task is a terminator task"""
        return self.request_task_address == TERMINATOR_ADDRESS

    @classmethod
    def allowed_action_types(cls) -> List[str]:
        return [e.value for e in ActionType]

    def get_cached_task_id(self) -> Optional[str]:
        """Gets the cached celery task ID for this request task."""
        cache: FidesopsRedis = get_cache()
        task_id = cache.get(get_async_task_tracking_cache_key(self.id))
        return task_id

    def cleanup_external_storage(self) -> None:
        """Clean up all external storage files for this request task"""
        # Access the descriptor from the class to call cleanup
        RequestTask.access_data.cleanup(self)
        RequestTask.data_for_erasures.cleanup(self)

    def get_access_data(self) -> List[Row]:
        """Helper to retrieve access data or default to empty list"""
        return self.access_data or []

    def get_data_for_erasures(self) -> List[Row]:
        """Helper to retrieve erasure data needed to build masking requests or default to empty list"""
        return self.data_for_erasures or []

    def delete(self, db: Session) -> None:
        """Override delete to cleanup external storage first"""
        self.cleanup_external_storage()
        super().delete(db)

    def update_status(self, db: Session, status: ExecutionLogStatus) -> None:
        """Helper method to update a task's status"""
        self.status = status
        self.save(db)

    def get_tasks_with_same_action_type(
        self, db: Session, collection_address_str: str
    ) -> Query:
        """Fetch task on the same privacy request and action type as current by collection address"""
        return db.query(RequestTask).filter(
            RequestTask.privacy_request_id == self.privacy_request_id,
            RequestTask.action_type == self.action_type,
            RequestTask.collection_address == collection_address_str,
        )

    def get_pending_downstream_tasks(self, db: Session) -> Query:
        """Returns the immediate downstream task objects that are still pending"""
        return db.query(RequestTask).filter(
            RequestTask.privacy_request_id == self.privacy_request_id,
            RequestTask.action_type == self.action_type,
            RequestTask.collection_address.in_(self.downstream_tasks or []),
            RequestTask.status == ExecutionLogStatus.pending,
        )

    def can_queue_request_task(self, db: Session, should_log: bool = False) -> bool:
        """Returns True if upstream tasks are complete and the current Request Task
        is not running in another celery task.

        This check ignores its database status - that is checked elsewhere.
        """
        return self.upstream_tasks_complete(
            db, should_log
        ) and not self.request_task_running(should_log)

    def upstream_tasks_complete(self, db: Session, should_log: bool = False) -> bool:
        """Determines if all of the upstream tasks of the current task are complete"""
        upstream_tasks: Query = self.upstream_tasks_objects(db)
        tasks_complete: bool = all(
            upstream_task.status in COMPLETED_EXECUTION_LOG_STATUSES
            for upstream_task in upstream_tasks
        ) and upstream_tasks.count() == len(self.upstream_tasks or [])

        if not tasks_complete and should_log:
            logger.debug(
                "Upstream tasks incomplete for {} task {}.",
                self.action_type,
                self.collection_address,
            )

        return tasks_complete

    def upstream_tasks_objects(self, db: Session) -> Query:
        """Returns Request Task objects that are upstream of the current Request Task"""
        upstream_tasks: Query = db.query(RequestTask).filter(
            RequestTask.privacy_request_id == self.privacy_request_id,
            RequestTask.collection_address.in_(self.upstream_tasks or []),
            RequestTask.action_type == self.action_type,
        )
        return upstream_tasks

    def request_task_running(self, should_log: bool = False) -> bool:
        """Returns a rough measure if the Request Task is already running -
        not 100% accurate.

        This is further only applicable if you are running workers and
        CONFIG.execution.task_always_eager=False. This is just an extra check to reduce possible
        over-scheduling, but it is also okay if the same node runs multiple times.
        """
        celery_task_id: Optional[str] = self.get_cached_task_id()
        if not celery_task_id:
            return False

        if should_log:
            logger.debug(
                "Celery Task ID {} found for {} task {}.",
                celery_task_id,
                self.action_type,
                self.collection_address,
            )

        task_in_flight: bool = celery_tasks_in_flight([celery_task_id])

        if task_in_flight and should_log:
            logger.debug(
                "Celery Task {} already processing for {} task {}.",
                celery_task_id,
                self.action_type,
                self.collection_address,
            )

        return task_in_flight


class RequestTaskSubRequest(Base):
    """
    Model for storing individual sub-request data during the execution of a request task.
    Supports 1:N relationship - each RequestTask can have multiple sub-requests.
    Currently used for storing request data for polling tasks.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "request_task_sub_request"

    request_task_id = Column(
        String(255),
        ForeignKey(
            "requesttask.id",
            name="request_task_sub_request_request_task_id_fkey",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    request_task = relationship(
        "RequestTask",
        back_populates="sub_requests",
    )

    # Individual sub-request data (e.g., request_id, status, result data)
    # Additional fields for enhanced sub-request tracking
    param_values = Column(  # An encrypted JSON String - saved as a dict
        StringEncryptedType(
            type_in=JSONTypeOverride,
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
        nullable=False,
    )
    status = Column(String, nullable=False)

    # Raw data retrieved from an access request is stored here.  This contains all of the
    # intermediate data we retrieved, needed for downstream tasks, but hasn't been filtered
    # by data category for the end user.
    _access_data = Column(  # An encrypted JSON String - saved as a list of Rows
        "access_data",
        StringEncryptedType(
            type_in=JSONTypeOverride,
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
    )

    # Use descriptors for automatic external storage handling
    access_data = EncryptedLargeDataDescriptor(
        field_name="access_data", empty_default=[]
    )

    # Written after an erasure is completed
    rows_masked = Column(Integer)

    def get_correlation_id(self) -> Optional[str]:
        """Helper method to extract correlation_id from param_values."""
        if self.param_values and "request_id" in self.param_values:
            return self.param_values["request_id"]
        return None

    def update_status(self, db: Session, status: str) -> None:
        """Helper method to update the status of this sub-request."""
        self.status = status
        self.save(db)

    def cleanup_external_storage(self) -> None:
        """Clean up all external storage files for this sub-request"""
        # Access the descriptor from the class to call cleanup
        RequestTaskSubRequest.access_data.cleanup(self)

    def get_access_data(self) -> List[Row]:
        """Helper to retrieve access data or default to empty list"""
        return self.access_data or []

    def delete(self, db: Session) -> None:
        """Override delete to cleanup external storage first"""
        self.cleanup_external_storage()
        super().delete(db)
