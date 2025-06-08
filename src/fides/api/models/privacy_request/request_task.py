# pylint: disable=R0401, C0302

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

from loguru import logger
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Query, Session, relationship
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.api.deps import get_autoclose_db_session
from fides.api.db.base_class import Base, JSONTypeOverride  # type: ignore[attr-defined]
from fides.api.db.util import EnumColumn
from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
)
from fides.api.models.privacy_request.execution_log import (
    COMPLETED_EXECUTION_LOG_STATUSES,
)
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import ExecutionLogStatus
from fides.api.schemas.request_task.external_storage import ExternalStorageMetadata
from fides.api.util.cache import (
    FidesopsRedis,
    celery_tasks_in_flight,
    get_async_task_tracking_cache_key,
    get_cache,
)
from fides.api.util.collection_util import Row
from fides.api.util.request_task_storage_util import (
    RequestTaskStorageError,
    RequestTaskStorageUtil,
)
from fides.api.util.request_task_util import (
    LARGE_DATA_THRESHOLD_BYTES,
    calculate_data_size,
    is_large_data,
)
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


class RequestTask(Base):
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
    action_type = Column(EnumColumn(ActionType), nullable=False, index=True)

    # Note that RequestTasks share statuses with ExecutionLogs.  When a RequestTask changes state, an ExecutionLog
    # is also created with that state.  These are tied tightly together in GraphTask.
    status = Column(
        EnumColumn(
            ExecutionLogStatus,
            native_enum=False,
            values_callable=lambda x: [
                i.value for i in x
            ],  # Using ExecutionLogStatus values in database, even though app is using the names.
        ),  # character varying in database
        index=True,
        nullable=False,
    )

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

    # Written after an erasure is completed
    rows_masked = Column(Integer)
    # Written after a consent request is completed - not all consent
    # connectors will end up sending a request
    consent_sent = Column(Boolean)

    # For async tasks awaiting callback
    callback_succeeded = Column(Boolean)

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

    def get_cached_task_id(self) -> Optional[str]:
        """Gets the cached celery task ID for this request task."""
        cache: FidesopsRedis = get_cache()
        task_id = cache.get(get_async_task_tracking_cache_key(self.id))
        return task_id

    def _store_large_data(
        self,
        db: Session,
        data: List[Row],
        data_type: str,
        storage_key: Optional[str] = None,
    ) -> ExternalStorageMetadata:
        """Store large data in external storage and return metadata

        Args:
            db: Database session
            data: The data to store
            data_type: Type of data being stored ("access_data" or "data_for_erasures")
            storage_key: Optional specific storage config key to use, defaults to active default

        Returns:
            ExternalStorageMetadata with storage details
        """
        return RequestTaskStorageUtil.store_large_data(
            db=db,
            privacy_request_id=self.privacy_request_id,  # type: ignore[arg-type]
            collection_name=self.collection_name,
            data=data,
            data_type=data_type,
            storage_key=storage_key,
        )

    def _retrieve_large_data(
        self, db: Session, metadata: ExternalStorageMetadata
    ) -> List[Row]:
        """Retrieve large data from external storage"""
        return RequestTaskStorageUtil.retrieve_large_data(db=db, metadata=metadata)

    def _delete_large_data(
        self, db: Session, metadata: ExternalStorageMetadata
    ) -> None:
        """Delete large data from external storage"""
        RequestTaskStorageUtil.delete_large_data(db=db, metadata=metadata)

    @property
    def access_data(self) -> Optional[List[Row]]:
        """Get access data, handling both direct storage and external storage"""
        raw_data = self._access_data
        if raw_data is None:
            return None

        # Check if it's metadata (dict with storage info) or actual data (list)
        if isinstance(raw_data, dict) and "storage_type" in raw_data:
            # It's external storage metadata
            logger.info(
                f"Reading access_data from external storage ({raw_data.get('storage_type')})"
            )
            try:
                metadata = ExternalStorageMetadata.model_validate(raw_data)
                with get_autoclose_db_session() as session:
                    data = self._retrieve_large_data(session, metadata)
                logger.info(
                    f"Successfully retrieved {len(data)} records from external storage"
                )
                return data
            except Exception as e:
                logger.error(
                    f"Failed to retrieve access_data from external storage: {str(e)}"
                )
                raise RequestTaskStorageError(
                    f"Failed to retrieve access_data: {str(e)}"
                ) from e
        else:
            return raw_data

    @access_data.setter
    def access_data(self, value: Optional[List[Row]]) -> None:
        """Set access data, automatically using external storage for large data"""
        if not value:
            # Clean up any existing external storage
            self._cleanup_external_access_data()
            self._access_data = []
            return

        # Check if data is large enough for external storage
        if is_large_data(value):
            logger.info(
                f"Data size ({calculate_data_size(value)} bytes) exceeds threshold "
                f"({LARGE_DATA_THRESHOLD_BYTES} bytes), storing externally"
            )
            # Clean up any existing external storage first
            self._cleanup_external_access_data()

            # Store in external storage
            with get_autoclose_db_session() as session:
                metadata = self._store_large_data(session, value, "access_data")
                self._access_data = metadata.model_dump()
        else:
            # Clean up any existing external storage
            self._cleanup_external_access_data()
            # Store directly in database
            self._access_data = value

    @property
    def data_for_erasures(self) -> Optional[List[Row]]:
        """Get data for erasures, handling both direct storage and external storage"""
        raw_data = self._data_for_erasures
        if raw_data is None:
            return None

        # Check if it's metadata (dict with storage info) or actual data (list)
        if isinstance(raw_data, dict) and "storage_type" in raw_data:
            # It's external storage metadata
            logger.info(
                f"Reading data_for_erasures from external storage ({raw_data.get('storage_type')})"
            )
            try:
                metadata = ExternalStorageMetadata.model_validate(raw_data)
                with get_autoclose_db_session() as session:
                    data = self._retrieve_large_data(session, metadata)
                logger.info(
                    f"Successfully retrieved {len(data)} records from external storage"
                )
                return data
            except Exception as e:
                logger.error(
                    f"Failed to retrieve data_for_erasures from external storage: {str(e)}"
                )
                raise RequestTaskStorageError(
                    f"Failed to retrieve data_for_erasures: {str(e)}"
                ) from e
        else:
            return raw_data

    @data_for_erasures.setter
    def data_for_erasures(self, value: Optional[List[Row]]) -> None:
        """Set data for erasures, automatically using external storage for large data"""
        if not value:
            # Clean up any existing external storage
            self._cleanup_external_data_for_erasures()
            self._data_for_erasures = []
            return

        # Check if data is large enough for external storage
        if is_large_data(value):
            logger.info(
                f"Data size ({calculate_data_size(value)} bytes) exceeds threshold "
                f"({LARGE_DATA_THRESHOLD_BYTES} bytes), storing externally"
            )
            # Clean up any existing external storage first
            self._cleanup_external_data_for_erasures()

            # Store in external storage
            with get_autoclose_db_session() as session:
                metadata = self._store_large_data(session, value, "data_for_erasures")
                self._data_for_erasures = metadata.model_dump()
        else:
            # Clean up any existing external storage
            self._cleanup_external_data_for_erasures()
            # Store directly in database
            self._data_for_erasures = value

    def _cleanup_external_access_data(self) -> None:
        """Clean up external storage for access_data if it exists"""
        if isinstance(self._access_data, dict) and "storage_type" in self._access_data:
            try:
                metadata = ExternalStorageMetadata.model_validate(self._access_data)
                with get_autoclose_db_session() as session:
                    self._delete_large_data(session, metadata)
            except Exception as e:
                logger.warning(f"Failed to cleanup external access_data: {str(e)}")

    def _cleanup_external_data_for_erasures(self) -> None:
        """Clean up external storage for data_for_erasures if it exists"""
        if (
            isinstance(self._data_for_erasures, dict)
            and "storage_type" in self._data_for_erasures
        ):
            try:
                metadata = ExternalStorageMetadata.model_validate(
                    self._data_for_erasures
                )
                with get_autoclose_db_session() as session:
                    self._delete_large_data(session, metadata)
            except Exception as e:
                logger.warning(
                    f"Failed to cleanup external data_for_erasures: {str(e)}"
                )

    def cleanup_external_storage(self) -> None:
        """Clean up all external storage files for this request task"""
        self._cleanup_external_access_data()
        self._cleanup_external_data_for_erasures()

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
                self.action_type.value,
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
                self.action_type.value,
                self.collection_address,
            )

        task_in_flight: bool = celery_tasks_in_flight([celery_task_id])

        if task_in_flight and should_log:
            logger.debug(
                "Celery Task {} already processing for {} task {}.",
                celery_task_id,
                self.action_type.value,
                self.collection_address,
            )

        return task_in_flight
