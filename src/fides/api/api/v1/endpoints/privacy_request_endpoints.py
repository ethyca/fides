# pylint: disable=too-many-lines

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import (
    Annotated,
    Any,
    DefaultDict,
    Dict,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Union,
)

import sqlalchemy
from fastapi import BackgroundTasks, Body, Depends, HTTPException, Security
from fastapi.encoders import jsonable_encoder
from fastapi.params import Query as FastAPIQuery
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from pydantic import Field
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import cast, null
from sqlalchemy.orm import Query, Session, selectinload
from starlette.responses import StreamingResponse
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api import deps
from fides.api.api.v1.endpoints.dataset_config_endpoints import _get_connection_config
from fides.api.api.v1.endpoints.manual_webhook_endpoints import (
    get_access_manual_webhook_or_404,
)
from fides.api.common_exceptions import (
    FidesopsException,
    IdentityVerificationException,
    ManualWebhookFieldsUnset,
    NoCachedManualWebhookEntry,
    PrivacyRequestError,
    TraversalError,
    ValidationError,
)
from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.audit_log import AuditLog
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.manual_webhook import AccessManualWebhook
from fides.api.models.policy import Policy, PolicyPreWebhook, Rule
from fides.api.models.pre_approval_webhook import (
    PreApprovalWebhook,
    PreApprovalWebhookReply,
)
from fides.api.models.privacy_request import (
    EXITED_EXECUTION_LOG_STATUSES,
    ExecutionLog,
    PrivacyRequest,
    PrivacyRequestNotifications,
    RequestTask,
)
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.oauth.utils import (
    verify_callback_oauth_policy_pre_webhook,
    verify_callback_oauth_pre_approval_webhook,
    verify_oauth_client,
    verify_request_task_callback,
)
from fides.api.schemas.api import ResponseWithMessage
from fides.api.schemas.dataset import CollectionAddressResponse, DryRunDatasetResponse
from fides.api.schemas.external_https import PrivacyRequestResumeFormat
from fides.api.schemas.policy import ActionType, CurrentStep
from fides.api.schemas.privacy_request import (
    BULK_PRIVACY_REQUEST_BATCH_SIZE,
    BulkPostPrivacyRequests,
    BulkReviewResponse,
    BulkSoftDeletePrivacyRequests,
    CancelPrivacyRequestSelection,
    CheckpointActionRequired,
    DenyPrivacyRequestSelection,
    ExecutionLogDetailResponse,
    FilteredPrivacyRequestResults,
    LogEntry,
    ManualWebhookData,
    PrivacyRequestAccessResults,
    PrivacyRequestBulkSelection,
    PrivacyRequestCreate,
    PrivacyRequestFilter,
    PrivacyRequestNotificationInfo,
    PrivacyRequestResponse,
    PrivacyRequestSource,
    PrivacyRequestStatus,
    PrivacyRequestTaskSchema,
    PrivacyRequestVerboseResponse,
    RequestTaskCallbackRequest,
    VerificationCode,
)
from fides.api.service.deps import get_messaging_service, get_privacy_request_service
from fides.api.service.messaging.message_dispatch_service import EMAIL_JOIN_STRING
from fides.api.service.privacy_request.email_batch_service import send_email_batch
from fides.api.task.execute_request_tasks import log_task_queued, queue_request_task
from fides.api.task.filter_results import filter_data_categories
from fides.api.task.graph_task import EMPTY_REQUEST, EMPTY_REQUEST_TASK, collect_queries
from fides.api.task.task_resources import TaskResources
from fides.api.util.api_router import APIRouter
from fides.api.util.cache import FidesopsRedis, get_cache
from fides.api.util.collection_util import Row
from fides.api.util.endpoint_utils import validate_start_and_end_filters
from fides.api.util.enums import ColumnSort
from fides.api.util.storage_util import StorageJSONEncoder
from fides.common.api.scope_registry import (
    PRIVACY_REQUEST_CALLBACK_RESUME,
    PRIVACY_REQUEST_CREATE,
    PRIVACY_REQUEST_DELETE,
    PRIVACY_REQUEST_EMAIL_INTEGRATIONS_SEND,
    PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_NOTIFICATIONS_READ,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_READ_ACCESS_RESULTS,
    PRIVACY_REQUEST_REVIEW,
    PRIVACY_REQUEST_TRANSFER,
    PRIVACY_REQUEST_UPLOAD_DATA,
    PRIVACY_REQUEST_VIEW_DATA,
)
from fides.common.api.v1.urn_registry import (
    PRIVACY_REQUEST_ACCESS_RESULTS,
    PRIVACY_REQUEST_APPROVE,
    PRIVACY_REQUEST_AUTHENTICATED,
    PRIVACY_REQUEST_BATCH_EMAIL_SEND,
    PRIVACY_REQUEST_BULK_FINALIZE,
    PRIVACY_REQUEST_BULK_RETRY,
    PRIVACY_REQUEST_BULK_SOFT_DELETE,
    PRIVACY_REQUEST_CANCEL,
    PRIVACY_REQUEST_DENY,
    PRIVACY_REQUEST_FILTERED_RESULTS,
    PRIVACY_REQUEST_FINALIZE,
    PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT,
    PRIVACY_REQUEST_MANUAL_WEBHOOK_ERASURE_INPUT,
    PRIVACY_REQUEST_NOTIFICATIONS,
    PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE,
    PRIVACY_REQUEST_PRE_APPROVE_NOT_ELIGIBLE,
    PRIVACY_REQUEST_REQUEUE,
    PRIVACY_REQUEST_RESUBMIT,
    PRIVACY_REQUEST_RESUME,
    PRIVACY_REQUEST_RESUME_FROM_REQUIRES_INPUT,
    PRIVACY_REQUEST_RETRY,
    PRIVACY_REQUEST_SEARCH,
    PRIVACY_REQUEST_SOFT_DELETE,
    PRIVACY_REQUEST_TRANSFER_TO_PARENT,
    PRIVACY_REQUEST_VERIFY_IDENTITY,
    PRIVACY_REQUESTS,
    REQUEST_PREVIEW,
    REQUEST_STATUS_LOGS,
    REQUEST_TASK_CALLBACK,
    REQUEST_TASKS,
    V1_URL_PREFIX,
)
from fides.config import CONFIG
from fides.config.config_proxy import ConfigProxy
from fides.service.dataset.dataset_config_service import (
    replace_references_with_identities,
)
from fides.service.messaging.messaging_service import MessagingService
from fides.service.privacy_request.privacy_request_service import (
    PrivacyRequestService,
    _process_privacy_request_restart,
    _requeue_privacy_request,
    handle_approval,
    queue_privacy_request,
)

router = APIRouter(tags=["Privacy Requests"], prefix=V1_URL_PREFIX)

EMBEDDED_EXECUTION_LOG_LIMIT = 50


def get_privacy_request_or_error(
    db: Session, privacy_request_id: str, error_if_deleted: Optional[bool] = True
) -> PrivacyRequest:
    """Load the privacy request or throw a 404"""
    logger.debug("Finding privacy request with id '{}'", privacy_request_id)
    privacy_request_service = PrivacyRequestService(
        db, ConfigProxy(db), MessagingService(db, CONFIG, ConfigProxy(db))
    )
    privacy_request = privacy_request_service.get_privacy_request(privacy_request_id)

    if not privacy_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No privacy request found with id '{privacy_request_id}'.",
        )

    if error_if_deleted and privacy_request.deleted_at is not None:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Privacy request with id {privacy_request_id} has been deleted.",
        )

    return privacy_request


def validate_filters(filters: PrivacyRequestFilter) -> None:
    if any([filters.completed_lt, filters.completed_gt]) and any(
        [filters.errored_lt, filters.errored_gt]
    ):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Cannot specify both succeeded and failed query params.",
        )
    validate_start_and_end_filters(
        [
            (filters.created_lt, filters.created_gt, "created"),
            (filters.completed_lt, filters.completed_gt, "completed"),
            (filters.errored_lt, filters.errored_gt, "errored"),
            (filters.started_lt, filters.started_gt, "started"),
        ]
    )


@router.post(
    PRIVACY_REQUESTS,
    status_code=HTTP_200_OK,
    response_model=BulkPostPrivacyRequests,
)
def create_privacy_request(
    *,
    privacy_request_service: PrivacyRequestService = Depends(
        get_privacy_request_service
    ),
    data: Annotated[
        List[PrivacyRequestCreate], Field(max_length=BULK_PRIVACY_REQUEST_BATCH_SIZE)
    ],  # type: ignore
) -> BulkPostPrivacyRequests:
    """
    Given a list of privacy request data elements, create corresponding PrivacyRequest objects
    or report failure and execute them within the Fidesops system.
    You cannot update privacy requests after they've been created.
    """
    return privacy_request_service.create_bulk_privacy_requests(
        data, authenticated=False
    )


@router.post(
    PRIVACY_REQUEST_AUTHENTICATED,
    status_code=HTTP_200_OK,
    response_model=BulkPostPrivacyRequests,
)
def create_privacy_request_authenticated(
    *,
    privacy_request_service: PrivacyRequestService = Depends(
        get_privacy_request_service
    ),
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[PRIVACY_REQUEST_CREATE],
    ),
    data: Annotated[
        List[PrivacyRequestCreate], Field(max_length=BULK_PRIVACY_REQUEST_BATCH_SIZE)
    ],  # type: ignore
) -> BulkPostPrivacyRequests:
    """
    Given a list of privacy request data elements, create corresponding PrivacyRequest objects
    or report failure and execute them within the Fidesops system.
    You cannot update privacy requests after they've been created.
    This route requires authentication instead of using verification codes.
    """

    return privacy_request_service.create_bulk_privacy_requests(
        data, authenticated=True, user_id=client.user_id
    )


def execution_and_audit_logs_by_dataset_name(
    self: PrivacyRequest,
) -> DefaultDict[str, List[Union["AuditLog", "ExecutionLog"]]]:
    """
    Returns a combined mapping of execution and audit logs for the given privacy request.

    Audit Logs are for the entire privacy request as a whole, while execution logs are created for specific collections.
    Logs here are grouped by dataset, but if it is an audit log, it is just given a fake dataset name, here "Request + status"
    ExecutionLogs for each dataset are truncated.

    Added as a conditional property to the PrivacyRequest class at runtime to
    show optionally embedded execution and audit logs.

    An example response might include your execution logs from your mongo db in one group, and execution logs from
    your postgres db in a different group, plus audit logs for when the request was approved and denied.
    """
    db: Session = Session.object_session(self)
    all_logs: DefaultDict[str, List[Union["AuditLog", "ExecutionLog"]]] = defaultdict(
        list
    )

    execution_log_query: Query = db.query(
        ExecutionLog.id,
        ExecutionLog.created_at,
        ExecutionLog.updated_at,
        ExecutionLog.message,
        cast(ExecutionLog.status, sqlalchemy.String).label(
            "status"
        ),  # Casting to string so we can perform a union of execution log and audit log statuses
        ExecutionLog.privacy_request_id,
        ExecutionLog.dataset_name,
        ExecutionLog.collection_name,
        ExecutionLog.connection_key,
        ExecutionLog.fields_affected,
        ExecutionLog.action_type,
        null().label("user_id"),
    ).filter(ExecutionLog.privacy_request_id == self.id)

    audit_log_query: Query = db.query(
        AuditLog.id,
        AuditLog.created_at,
        AuditLog.updated_at,
        AuditLog.message,
        cast(AuditLog.action.label("status"), sqlalchemy.String).label(
            "status"
        ),  # Casting to string so we can perform a union of execution log and audit log statuses
        AuditLog.privacy_request_id,
        null().label("dataset_name"),
        null().label("collection_name"),
        null().label("connection_key"),
        null().label("fields_affected"),
        null().label("action_type"),
        AuditLog.user_id,
    ).filter(AuditLog.privacy_request_id == self.id)

    combined: Query = execution_log_query.union_all(audit_log_query)

    for log in combined.order_by(ExecutionLog.updated_at.asc()):
        dataset_name: str = log.dataset_name or f"Request {log.status}"

        if len(all_logs[dataset_name]) > EMBEDDED_EXECUTION_LOG_LIMIT - 1:
            continue
        all_logs[dataset_name].append(log)
    return all_logs


def attach_resume_instructions(privacy_request: PrivacyRequest) -> None:
    """
    Temporarily update a paused/errored/requires_input privacy request object with instructions from the Redis cache
    about how to resume manually if applicable.
    """
    resume_endpoint: Optional[str] = None
    action_required_details: Optional[CheckpointActionRequired] = None

    if privacy_request.status == PrivacyRequestStatus.paused:
        # Graph is paused on a pre-processing webhook
        resume_endpoint = PRIVACY_REQUEST_RESUME

    elif privacy_request.status == PrivacyRequestStatus.error:
        action_required_details = privacy_request.get_failed_checkpoint_details()
        resume_endpoint = PRIVACY_REQUEST_RETRY

    elif privacy_request.status == PrivacyRequestStatus.requires_input:
        # No action required details because this doesn't need to resume from a
        # specific step or collection
        resume_endpoint = PRIVACY_REQUEST_RESUME_FROM_REQUIRES_INPUT

    if action_required_details:
        action_required_details.step = action_required_details.step.value  # type: ignore
        action_required_details.collection = (
            action_required_details.collection.value
            if action_required_details.collection
            else None  # type: ignore
        )

    privacy_request.action_required_details = action_required_details
    # replaces the placeholder in the url with the privacy request id
    privacy_request.resume_endpoint = (
        resume_endpoint.format(privacy_request_id=privacy_request.id)
        if resume_endpoint
        else None
    )


def _validate_result_size(query: Query) -> None:
    """
    Validates the result size is less than maximum allowed by settings.
    Raises an HTTPException if result size is greater than maximum.
    Result size is determined by running an up-front "count" query.
    """
    row_count = query.count()
    max_rows = CONFIG.admin_ui.max_privacy_request_download_rows
    if row_count > max_rows:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Requested privacy request report would contain {row_count} rows. A maximum of {max_rows} rows is permitted. Please narrow your date range and try again.",
        )


def _shared_privacy_request_search(
    *,
    db: Session,
    params: Params,
    filters: PrivacyRequestFilter,
    privacy_request_service: PrivacyRequestService,
    identity: Optional[str] = None,
) -> Union[StreamingResponse, AbstractPage[PrivacyRequest]]:
    """
    Internal function to handle the logic for retrieving privacy requests.

    This function is used by both the GET and POST versions of the privacy request endpoints
    to avoid duplicating the logic while transitioning from the GET version to the
    POST version of the endpoint.
    """

    logger.debug("Finding all request statuses with pagination params {}", params)
    validate_filters(filters)

    # Use query_without_large_columns to prevent OOM errors when loading many privacy requests
    query = privacy_request_service.filter_privacy_requests(
        PrivacyRequest.query_without_large_columns(db),
        filters=filters,
        identity=identity,
    )

    logger.debug(
        "Sorting requests by field: {} and direction: {}",
        filters.sort_field,
        filters.sort_direction,
    )
    if hasattr(PrivacyRequest, filters.sort_field) is False:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{filters.sort_field} is not on PrivacyRequest",
        )
    query = privacy_request_service.sort_privacy_requests(
        query, filters.sort_field, filters.sort_direction
    )

    if filters.download_csv:
        _validate_result_size(query)
        # Eager load relationships needed for CSV export to avoid N+1 queries
        query = query.options(
            selectinload(PrivacyRequest.provided_identities),  # type: ignore[attr-defined]
            selectinload(PrivacyRequest.custom_fields),  # type: ignore[attr-defined]
            selectinload(PrivacyRequest.policy).selectinload(Policy.rules),  # type: ignore[attr-defined]
        )
        # Returning here if download_csv param was specified
        logger.info("Downloading privacy requests as csv")
        return privacy_request_service.download_privacy_requests_csv(query)

    # Eager load relationships for regular list view to avoid N+1 queries
    if filters.include_identities or filters.include_custom_privacy_request_fields:
        eager_load_options = []
        if filters.include_identities:
            eager_load_options.append(
                selectinload(PrivacyRequest.provided_identities)  # type: ignore[attr-defined]
            )
        if filters.include_custom_privacy_request_fields:
            eager_load_options.append(
                selectinload(PrivacyRequest.custom_fields)  # type: ignore[attr-defined]
            )
        query = query.options(*eager_load_options)

    # Conditionally embed execution log details in the response.
    if filters.verbose:
        logger.info("Finding execution and audit log details")
        PrivacyRequest.execution_and_audit_logs_by_dataset = property(
            execution_and_audit_logs_by_dataset_name
        )
    else:
        PrivacyRequest.execution_and_audit_logs_by_dataset = property(lambda self: None)

    paginated = paginate(query, params)

    for item in paginated.items:  # type: ignore
        if filters.include_identities:
            item.identity = item.get_persisted_identity().labeled_dict(
                include_default_labels=True
            )

        if filters.include_custom_privacy_request_fields:
            item.custom_privacy_request_fields = (
                item.get_persisted_custom_privacy_request_fields()
            )

        attach_resume_instructions(item)

    return paginated


@router.get(
    PRIVACY_REQUESTS,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_READ])],
    response_model=Page[
        Union[
            PrivacyRequestVerboseResponse,
            PrivacyRequestResponse,
        ]
    ],
    deprecated=True,
)
def get_request_status(
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    request_id: Optional[str] = None,
    identity: Optional[str] = None,
    status: Optional[List[PrivacyRequestStatus]] = FastAPIQuery(default=None),  # type:ignore
    fuzzy_search_str: Optional[str] = None,
    created_lt: Optional[datetime] = None,
    created_gt: Optional[datetime] = None,
    started_lt: Optional[datetime] = None,
    started_gt: Optional[datetime] = None,
    completed_lt: Optional[datetime] = None,
    completed_gt: Optional[datetime] = None,
    errored_lt: Optional[datetime] = None,
    errored_gt: Optional[datetime] = None,
    external_id: Optional[str] = None,
    location: Optional[str] = None,
    action_type: Optional[ActionType] = None,
    verbose: Optional[bool] = False,
    include_identities: Optional[bool] = False,
    include_custom_privacy_request_fields: Optional[bool] = False,
    download_csv: Optional[bool] = False,
    include_deleted_requests: Optional[bool] = False,
    sort_field: str = "created_at",
    sort_direction: ColumnSort = ColumnSort.DESC,
) -> Union[StreamingResponse, AbstractPage[PrivacyRequest]]:
    """
    **This endpoint is deprecated. Please use `POST /privacy-request/search`,
    which uses body parameters instead of query parameters for filtering.**

    Returns PrivacyRequest information. Supports a variety of optional query params.

    To fetch a single privacy request, use the request_id query param `?request_id=`.
    To see individual execution logs, use the verbose query param `?verbose=True`.
    """

    # Build PrivacyRequestFilter from query parameters
    # Note: identities and custom_privacy_request_fields are only supported in the POST endpoint
    filters = PrivacyRequestFilter(
        request_id=request_id,
        fuzzy_search_str=fuzzy_search_str,
        identities=None,
        custom_privacy_request_fields=None,
        status=status,
        created_lt=created_lt,
        created_gt=created_gt,
        started_lt=started_lt,
        started_gt=started_gt,
        completed_lt=completed_lt,
        completed_gt=completed_gt,
        errored_lt=errored_lt,
        errored_gt=errored_gt,
        external_id=external_id,
        location=location,
        action_type=action_type,
        verbose=verbose,
        include_identities=include_identities,
        include_custom_privacy_request_fields=include_custom_privacy_request_fields,
        include_deleted_requests=include_deleted_requests,
        download_csv=download_csv,
        sort_field=sort_field,
        sort_direction=sort_direction,
    )
    privacy_request_service = PrivacyRequestService(
        db, ConfigProxy(db), MessagingService(db, CONFIG, ConfigProxy(db))
    )
    return _shared_privacy_request_search(
        db=db,
        params=params,
        filters=filters,
        privacy_request_service=privacy_request_service,
        identity=identity,
    )


@router.post(
    PRIVACY_REQUEST_SEARCH,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_READ])],
    response_model=Page[
        Union[
            PrivacyRequestVerboseResponse,
            PrivacyRequestResponse,
        ]
    ],
)
def privacy_request_search(
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    privacy_request_filter: Optional[PrivacyRequestFilter] = Body(None),
) -> Union[StreamingResponse, AbstractPage[PrivacyRequest]]:
    """
    Returns PrivacyRequest information. Supports a variety of optional filter parameters.

    To see individual execution logs, set `"verbose": true`.
    """

    # default filter if the payload is empty
    if privacy_request_filter is None:
        privacy_request_filter = PrivacyRequestFilter()

    privacy_request_service = PrivacyRequestService(
        db, ConfigProxy(db), MessagingService(db, CONFIG, ConfigProxy(db))
    )
    return _shared_privacy_request_search(
        db=db,
        params=params,
        filters=privacy_request_filter,
        privacy_request_service=privacy_request_service,
    )


@router.get(
    REQUEST_STATUS_LOGS,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_READ])],
    response_model=Page[ExecutionLogDetailResponse],
)
def get_request_status_logs(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
) -> AbstractPage[ExecutionLog]:
    """Returns all the execution logs associated with a given privacy request ordered by updated asc."""

    get_privacy_request_or_error(db, privacy_request_id, error_if_deleted=False)

    logger.debug(
        "Finding all execution logs for privacy request {} with params '{}'",
        privacy_request_id,
        params,
    )

    return paginate(
        ExecutionLog.query(db=db)
        .filter(ExecutionLog.privacy_request_id == privacy_request_id)
        .order_by(ExecutionLog.updated_at.asc()),
        params,
    )


@router.get(
    PRIVACY_REQUEST_NOTIFICATIONS,
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestNotificationInfo,
    dependencies=[
        Security(
            verify_oauth_client,
            scopes=[PRIVACY_REQUEST_NOTIFICATIONS_READ],
        )
    ],
)
def get_privacy_request_notification_info(
    *, db: Session = Depends(deps.get_db)
) -> PrivacyRequestNotificationInfo:
    """Retrieve privacy request notification email addresses and number of failures to trigger notifications."""
    info = PrivacyRequestNotifications.all(db)

    if not info:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No privacy request notification info found",
        )

    return PrivacyRequestNotificationInfo(
        email_addresses=[x for x in info[0].email.split(EMAIL_JOIN_STRING)],
        notify_after_failures=info[0].notify_after_failures,
    )


@router.put(
    PRIVACY_REQUEST_NOTIFICATIONS,
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestNotificationInfo,
    dependencies=[
        Security(
            verify_oauth_client,
            scopes=[PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE],
        )
    ],
)
def create_or_update_privacy_request_notifications(
    *, db: Session = Depends(deps.get_db), request_body: PrivacyRequestNotificationInfo
) -> PrivacyRequestNotificationInfo:
    """Create or update list of email addresses and number of failures for privacy request notifications."""
    # If email_addresses is empty it means notifications were turned off and the email
    # information should be deleted from the database. In this situation an empty list
    # of email address is returned along with the notify_after_failures sent from the
    # front end. This allows the first end to control the default notifiy_after_failures
    # number.
    if not request_body.email_addresses:
        all_notes = PrivacyRequestNotifications.all(db)
        try:
            note: PrivacyRequestNotifications = all_notes[0]
        except IndexError:
            pass
        else:
            note.delete(db=db)

        return PrivacyRequestNotificationInfo(
            email_addresses=[],
            notify_after_failures=request_body.notify_after_failures,
        )

    notification_info = {
        "email": EMAIL_JOIN_STRING.join(request_body.email_addresses),
        "notify_after_failures": request_body.notify_after_failures,
    }
    info_check: List[PrivacyRequestNotifications] = PrivacyRequestNotifications.all(
        db=db
    )
    info: PrivacyRequestNotifications
    try:
        info = info_check[0]
    except IndexError:
        info = PrivacyRequestNotifications.create(
            db=db,
            data=notification_info,
        )
    else:
        info.update(
            db=db,
            data=notification_info,
        )

    return PrivacyRequestNotificationInfo(
        email_addresses=info.email.split(", "),
        notify_after_failures=info.notify_after_failures,
    )


@router.put(
    REQUEST_PREVIEW,
    status_code=HTTP_200_OK,
    response_model=List[DryRunDatasetResponse],
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_READ])],
)
def get_request_preview_queries(
    *,
    db: Session = Depends(deps.get_db),
    dataset_keys: Optional[List[str]] = Body(None),
) -> List[DryRunDatasetResponse]:
    """Returns dry run queries given a list of dataset ids.  If a dataset references another dataset, both dataset
    keys must be in the request body."""
    dataset_configs: List[DatasetConfig] = []
    if not dataset_keys:
        dataset_configs = DatasetConfig.all(db=db)
        if not dataset_configs:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="No datasets could be found",
            )
    else:
        for dataset_key in dataset_keys:
            dataset_config = DatasetConfig.get_by(
                db=db, field="fides_key", value=dataset_key
            )
            if not dataset_config:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"No dataset with id '{dataset_key}'",
                )
            dataset_configs.append(dataset_config)
    try:
        connection_configs: List[ConnectionConfig] = []
        for dataset in dataset_configs:
            connection_config: Optional[ConnectionConfig] = ConnectionConfig.get(
                db=db, object_id=dataset.connection_config_id
            )
            if connection_config:
                connection_configs.append(connection_config)

        try:
            dataset_graph: DatasetGraph = DatasetGraph(
                *[dataset.get_graph() for dataset in dataset_configs]
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"{exc}. Make sure all referenced datasets are included in the request body.",
            )

        identity_seed: Dict[str, str] = {
            k: "something" for k in dataset_graph.identity_keys.values()
        }
        traversal: Traversal = Traversal(dataset_graph, identity_seed)

        queries: Dict[CollectionAddress, str] = collect_queries(
            traversal,
            TaskResources(
                EMPTY_REQUEST, Policy(), connection_configs, EMPTY_REQUEST_TASK, db
            ),
        )
        return [
            DryRunDatasetResponse(
                collectionAddress=CollectionAddressResponse(
                    dataset=key.dataset, collection=key.collection
                ),
                query=value,
            )
            for key, value in queries.items()
        ]
    except TraversalError as err:
        logger.info("Dry run failed: {}", err)
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Dry run failed",
        )


@router.post(
    PRIVACY_REQUEST_RESUME,
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestResponse,
)
def resume_privacy_request(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
    webhook: PolicyPreWebhook = Security(
        verify_callback_oauth_policy_pre_webhook,
        scopes=[PRIVACY_REQUEST_CALLBACK_RESUME],
    ),
    webhook_callback: PrivacyRequestResumeFormat,
) -> PrivacyRequestResponse:
    """Resume running a privacy request after it was paused by a Pre-Execution webhook"""
    privacy_request = get_privacy_request_or_error(db, privacy_request_id)
    # We don't want to persist derived identities because they have not been provided
    # by the end user
    privacy_request.cache_identity(webhook_callback.derived_identity)  # type: ignore

    if privacy_request.status != PrivacyRequestStatus.paused:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid resume request: privacy request '{privacy_request.id}' status = {privacy_request.status.value}.",
            # type: ignore
        )

    logger.info(
        "Resuming privacy request '{}' from webhook '{}'",
        privacy_request_id,
        webhook.key,
    )

    privacy_request.status = PrivacyRequestStatus.in_processing
    privacy_request.save(db=db)

    queue_privacy_request(
        privacy_request_id=privacy_request.id,
        from_webhook_id=webhook.id,
    )
    return privacy_request  # type: ignore[return-value]


def validate_manual_input(
    manual_rows: List[Row],
    collection: CollectionAddress,
    dataset_graph: DatasetGraph,
) -> None:
    """Validate manually-added data for a collection.

    The specified collection must exist and all fields must be previously defined.
    """
    for row in manual_rows:
        for field_name in row:
            if not dataset_graph.nodes[collection].collection.contains_field(
                lambda f: f.name == field_name  # pylint: disable=W0640
            ):
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Cannot save manual rows. No '{field_name}' field defined on the '{collection.value}' collection.",
                )


@router.post(
    PRIVACY_REQUEST_BULK_RETRY,
    status_code=HTTP_200_OK,
    response_model=BulkPostPrivacyRequests,
    dependencies=[
        Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
    ],
)
def bulk_restart_privacy_request_from_failure(
    privacy_requests: PrivacyRequestBulkSelection,
    *,
    db: Session = Depends(deps.get_db),
    privacy_request_service: PrivacyRequestService = Depends(
        get_privacy_request_service
    ),
) -> BulkPostPrivacyRequests:
    """
    Bulk restart privacy requests from failure.

    You can either provide explicit request_ids OR use filters to select privacy requests.
    When using filters, you can optionally exclude specific IDs via exclude_ids.

    For backwards compatibility, a plain list of request IDs is also accepted.
    """
    succeeded: List[PrivacyRequestResponse] = []
    failed: List[Dict[str, Any]] = []

    # Resolve request IDs from either explicit list or filters
    try:
        request_ids = privacy_request_service.resolve_request_ids(privacy_requests)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    batches = privacy_request_service.get_batches_for_bulk_operation(request_ids)

    # Fetch all privacy requests in one query to avoid N+1
    for batch in batches:
        privacy_requests_dict = {
            pr.id: pr
            for pr in PrivacyRequest.query_without_large_columns(db)
            .filter(PrivacyRequest.id.in_(batch))
            .all()
        }

        for privacy_request_id in batch:
            privacy_request = privacy_requests_dict.get(privacy_request_id)

            if not privacy_request:
                failed.append(
                    {
                        "message": f"No privacy request found with id '{privacy_request_id}'",
                        "data": {"privacy_request_id": privacy_request_id},
                    }
                )
                continue

            if privacy_request.deleted_at is not None:
                failed.append(
                    {
                        "message": "Cannot restart a deleted privacy request",
                        "data": {"privacy_request_id": privacy_request_id},
                    }
                )
                continue

            if privacy_request.status != PrivacyRequestStatus.error:
                failed.append(
                    {
                        "message": f"Cannot restart privacy request from failure: privacy request '{privacy_request.id}' status = {privacy_request.status.value}.",
                        "data": {"privacy_request_id": privacy_request_id},
                    }
                )
                continue

            failed_details: Optional[CheckpointActionRequired] = (
                privacy_request.get_failed_checkpoint_details()
            )

            succeeded.append(
                _process_privacy_request_restart(
                    privacy_request,
                    failed_details.step if failed_details else None,
                    db,
                )
            )

    return BulkPostPrivacyRequests(succeeded=succeeded, failed=failed)


@router.post(
    PRIVACY_REQUEST_RETRY,
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestResponse,
    dependencies=[
        Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
    ],
)
def restart_privacy_request_from_failure(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
    privacy_request_service: PrivacyRequestService = Depends(
        get_privacy_request_service
    ),
) -> PrivacyRequestResponse:
    """Restart a privacy request from failure"""
    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id
    )

    # Automatically resubmit the request if the cache has expired

    if (
        not privacy_request.verify_cache_for_identity_data()
        and privacy_request.status != PrivacyRequestStatus.complete
    ):
        logger.info(
            f"Cached data for privacy request {privacy_request.id} has expired, automatically resubmitting request"
        )
        return privacy_request_service.resubmit_privacy_request(privacy_request_id)  # type: ignore[return-value]

    if privacy_request.status != PrivacyRequestStatus.error:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot restart privacy request from failure: privacy request '{privacy_request.id}' status = {privacy_request.status.value}.",
            # type: ignore
        )

    failed_details: Optional[CheckpointActionRequired] = (
        privacy_request.get_failed_checkpoint_details()
    )

    return _process_privacy_request_restart(
        privacy_request,
        failed_details.step if failed_details else None,
        db,
    )


@router.post(
    PRIVACY_REQUEST_VERIFY_IDENTITY,
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestResponse,
)
def verify_identification_code(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
    config_proxy: ConfigProxy = Depends(deps.get_config_proxy),
    messaging_service: MessagingService = Depends(get_messaging_service),
    provided_code: VerificationCode,
) -> PrivacyRequestResponse:
    """Verify the supplied identity verification code.

    If successful, and we don't need a separate manual request approval, queue the privacy request
    for execution.

    Fires pre-approval webhooks if configured.
    """

    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id
    )
    try:
        privacy_request.verify_identity(db, provided_code.code)
        policy: Optional[Policy] = Policy.get(
            db=db, object_id=privacy_request.policy_id
        )
        messaging_service.send_privacy_request_receipt(
            policy, privacy_request.get_persisted_identity(), privacy_request
        )

    except IdentityVerificationException as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=exc.message)
    except PermissionError as exc:
        logger.info("Invalid verification code provided for {}.", privacy_request.id)
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=exc.args[0])

    logger.info("Identity verified for {}.", privacy_request.id)

    handle_approval(db, config_proxy, privacy_request)

    return privacy_request  # type: ignore[return-value]


@router.patch(
    PRIVACY_REQUEST_APPROVE,
    status_code=HTTP_200_OK,
    response_model=BulkReviewResponse,
)
def approve_privacy_request(
    privacy_requests: PrivacyRequestBulkSelection,
    *,
    db: Session = Depends(deps.get_db),
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[PRIVACY_REQUEST_REVIEW],
    ),
    privacy_request_service: PrivacyRequestService = Depends(
        get_privacy_request_service
    ),
) -> BulkReviewResponse:
    """
    Approve and dispatch a list of privacy requests and/or report failure.

    You can either provide explicit request_ids OR use filters to select privacy requests.
    When using filters, you can optionally exclude specific IDs via exclude_ids.

    For backwards compatibility, a plain list of request IDs is also accepted.

    Example with request_ids:
        {"request_ids": ["pri_123", "pri_456"]}

    Example with filters:
        {"filters": {"status": ["pending"]}, "exclude_ids": ["pri_789"]}
    """
    # Resolve request IDs from either explicit list or filters
    try:
        request_ids = privacy_request_service.resolve_request_ids(privacy_requests)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return privacy_request_service.approve_privacy_requests(
        request_ids, reviewed_by=client.user_id
    )


@router.patch(
    PRIVACY_REQUEST_DENY,
    status_code=HTTP_200_OK,
    response_model=BulkReviewResponse,
)
def deny_privacy_request(
    privacy_requests: DenyPrivacyRequestSelection,
    *,
    db: Session = Depends(deps.get_db),
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[PRIVACY_REQUEST_REVIEW],
    ),
    privacy_request_service: PrivacyRequestService = Depends(
        get_privacy_request_service
    ),
) -> BulkReviewResponse:
    """
    Deny a list of privacy requests and/or report failure.

    You can either provide explicit request_ids OR use filters to select privacy requests.
    When using filters, you can optionally exclude specific IDs via exclude_ids.

    For backwards compatibility, a plain list of request IDs is also accepted.
    """
    # Resolve request IDs from either explicit list or filters
    try:
        request_ids = privacy_request_service.resolve_request_ids(privacy_requests)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return privacy_request_service.deny_privacy_requests(
        request_ids, privacy_requests.reason, user_id=client.user_id
    )


@router.patch(
    PRIVACY_REQUEST_CANCEL,
    status_code=HTTP_200_OK,
    response_model=BulkReviewResponse,
)
def cancel_privacy_request(
    privacy_requests: CancelPrivacyRequestSelection,
    *,
    db: Session = Depends(deps.get_db),
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[PRIVACY_REQUEST_REVIEW],
    ),
    privacy_request_service: PrivacyRequestService = Depends(
        get_privacy_request_service
    ),
) -> BulkReviewResponse:
    """
    Cancel a list of privacy requests and/or report failure.

    You can either provide explicit request_ids OR use filters to select privacy requests.
    When using filters, you can optionally exclude specific IDs via exclude_ids.

    For backwards compatibility, a plain list of request IDs is also accepted.
    """
    # Resolve request IDs from either explicit list or filters
    try:
        request_ids = privacy_request_service.resolve_request_ids(privacy_requests)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return privacy_request_service.cancel_privacy_requests(
        request_ids, privacy_requests.reason, user_id=client.user_id
    )


def _validate_privacy_request_pending_or_error(
    db: Session, privacy_request_id: str
) -> None:
    privacy_request = (
        PrivacyRequest.query_without_large_columns(db)
        .filter(PrivacyRequest.id == privacy_request_id)
        .first()
    )
    if not privacy_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No privacy request found with id: '{privacy_request_id}'.",
        )

    if privacy_request.status != PrivacyRequestStatus.pending:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Privacy request with id '{privacy_request_id}' is not in pending status.",
        )


@router.post(
    PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE,
    status_code=HTTP_200_OK,
)
def mark_privacy_request_pre_approve_eligible(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
    privacy_request_service: PrivacyRequestService = Depends(
        get_privacy_request_service
    ),
    webhook: PreApprovalWebhook = Security(
        verify_callback_oauth_pre_approval_webhook, scopes=[PRIVACY_REQUEST_REVIEW]
    ),
) -> None:
    """
    Marks privacy request as eligible for automatic approval.
    If all webhook responses have been received and all are affirmative, proceed to queue privacy request
    """
    _validate_privacy_request_pending_or_error(db, privacy_request_id)
    logger.info(
        "Marking privacy request '{}' as eligible for automatic approval via webhook '{}' for connection config '{}'.",
        privacy_request_id,
        webhook.key,
        webhook.connection_config.key,
    )

    try:
        PreApprovalWebhookReply.create(
            db=db,
            data={
                "webhook_id": webhook.id,
                "privacy_request_id": privacy_request_id,
                "is_eligible": True,
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Failed to mark privacy request {privacy_request_id} as eligible due to: {str(exc)}",
        )

    all_webhooks = PreApprovalWebhook.all(db)

    def _reply_exists_for_webhook(webhook_id: str) -> bool:
        return bool(
            PreApprovalWebhookReply.filter(
                db=db,
                conditions=(
                    (PreApprovalWebhookReply.webhook_id == webhook_id)
                    & (PreApprovalWebhookReply.privacy_request_id == privacy_request_id)
                ),
            ).first()
        )

    # Check if not all replies have been received
    if not all(_reply_exists_for_webhook(webhook.id) for webhook in all_webhooks):
        # Subtlety here is that if a new webhook is configured between when the privacy request was created and when
        # the last webhook replied, then the privacy request can never be automatically approved. It must instead be
        # manually approved in the Admin UI.
        logger.info(
            "Not all pre-approval webhooks have responded for privacy request '{}'. Cannot automatically approve request.",
            privacy_request_id,
        )
        return

    # Check if all replies are true.  Reply ignored if its webhook has since been deleted.
    replies_for_privacy_request = (
        db.query(PreApprovalWebhookReply)
        .filter(
            PreApprovalWebhookReply.privacy_request_id == privacy_request_id,
            PreApprovalWebhookReply.webhook_id.isnot(None),
        )
        .all()
    )

    if not all(reply.is_eligible for reply in replies_for_privacy_request):
        logger.info(
            "Not all pre-approval webhooks have responded with eligible for privacy request '{}'. Cannot automatically approve request.",
            privacy_request_id,
        )
        return

    logger.info(
        "All pre-approval webhooks have responded with eligible for privacy request '{}'. Proceeding to automatically approve request.",
        privacy_request_id,
    )
    privacy_request_service.approve_privacy_requests(
        [privacy_request_id], webhook_id=webhook.id
    )


@router.post(
    PRIVACY_REQUEST_PRE_APPROVE_NOT_ELIGIBLE,
    status_code=HTTP_200_OK,
)
def mark_privacy_request_pre_approve_not_eligible(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
    webhook: PreApprovalWebhook = Security(
        verify_callback_oauth_pre_approval_webhook, scopes=[PRIVACY_REQUEST_REVIEW]
    ),
) -> None:
    """Marks privacy request as not eligible for automatic approval, regardless of what other webhook responses we receive"""
    _validate_privacy_request_pending_or_error(db, privacy_request_id)
    logger.info(
        "Marking privacy request '{}' as not eligible for automatic approval via webhook '{}' for connection config '{}'.",
        privacy_request_id,
        webhook.key,
        webhook.connection_config.key,
    )
    try:
        PreApprovalWebhookReply.create(
            db=db,
            data={
                "webhook_id": webhook.id,
                "privacy_request_id": privacy_request_id,
                "is_eligible": False,
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Failed to mark privacy request {privacy_request_id} as not eligible due to: {str(exc)}",
        )


def _handle_manual_webhook_input(
    action: Literal["access", "erasure"],
    connection_config: ConnectionConfig,
    privacy_request_id: str,
    db: Session,
    input_data: Dict[str, Any],
) -> None:
    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id
    )
    access_manual_webhook: AccessManualWebhook = get_access_manual_webhook_or_404(
        connection_config
    )

    if not privacy_request.status == PrivacyRequestStatus.requires_input:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid manual webhook {action} upload request: privacy request '{privacy_request.id}' status = {privacy_request.status.value}.",
            # type: ignore
        )

    try:
        getattr(privacy_request, f"cache_manual_webhook_{action}_input")(
            access_manual_webhook, input_data
        )
    except PydanticValidationError as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(exc.errors(include_url=False, include_input=False)),
        )

    logger.info(
        "{} input saved for manual webhook '{}' for privacy_request '{}'.",
        action.capitalize(),
        access_manual_webhook,
        privacy_request,
    )


@router.patch(
    PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_UPLOAD_DATA])],
    response_model=None,
)
def upload_manual_webhook_access_data(
    *,
    connection_config: ConnectionConfig = Depends(_get_connection_config),
    privacy_request_id: str,
    db: Session = Depends(deps.get_db),
    input_data: Dict[str, Any],
) -> None:
    """Upload manual access input for the privacy request for the fields defined on the access manual webhook.
    The data collected here is not included in the graph but uploaded directly to the user at the end
    of privacy request execution.

    Because a 'manual_webhook' ConnectionConfig has one AccessManualWebhook associated with it,
    we are using the ConnectionConfig key as the AccessManualWebhook identifier here.
    """
    _handle_manual_webhook_input(
        action="access",
        connection_config=connection_config,
        privacy_request_id=privacy_request_id,
        db=db,
        input_data=input_data,
    )


@router.patch(
    PRIVACY_REQUEST_MANUAL_WEBHOOK_ERASURE_INPUT,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_UPLOAD_DATA])],
    response_model=None,
)
def upload_manual_webhook_erasure_data(
    *,
    connection_config: ConnectionConfig = Depends(_get_connection_config),
    privacy_request_id: str,
    db: Session = Depends(deps.get_db),
    input_data: Dict[str, Any],
) -> None:
    """Upload manual erasure input for the privacy request for the fields defined on the access manual webhook.

    Because a 'manual_webhook' ConnectionConfig has one AccessManualWebhook associated with it,
    we are using the ConnectionConfig key as the AccessManualWebhook identifier here.
    """
    _handle_manual_webhook_input(
        action="erasure",
        connection_config=connection_config,
        privacy_request_id=privacy_request_id,
        db=db,
        input_data=input_data,
    )


@router.get(
    PRIVACY_REQUEST_TRANSFER_TO_PARENT,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_TRANSFER])],
    response_model=Dict[str, Optional[List[Row]]],
)
def privacy_request_data_transfer(
    *,
    privacy_request_id: str,
    rule_key: str,
    db: Session = Depends(deps.get_db),
    cache: FidesopsRedis = Depends(deps.get_cache),
) -> Dict[str, Optional[List[Row]]]:
    """Transfer access request information to the parent server."""
    privacy_request = PrivacyRequest.get(db=db, object_id=privacy_request_id)

    if not privacy_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No privacy request with id {privacy_request_id} found",
        )

    rule = Rule.filter(db=db, conditions=(Rule.key == rule_key)).first()  # pylint: disable=superfluous-parens
    if not rule:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Rule key {rule_key} not found",
        )

    access_result: Dict[str, Optional[List[Row]]] = (
        privacy_request.get_raw_access_results()
    )

    if not access_result:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No access request information found for privacy request id {privacy_request_id}",
        )
    datasets = DatasetConfig.all(db=db)
    if not datasets:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No datasets found for privacy request {privacy_request_id}",
        )

    dataset_graphs = [dataset_config.get_graph() for dataset_config in datasets]
    if not dataset_graphs:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No dataset graphs found for privacy request {privacy_request_id}",
        )
    dataset_graph = DatasetGraph(*dataset_graphs)
    target_categories = {target.data_category for target in rule.targets}
    filtered_results: Optional[Dict[str, Optional[List[Row]]]] = filter_data_categories(
        access_result,  # type: ignore
        target_categories,
        dataset_graph,
    )

    if filtered_results is None:
        raise HTTPException(
            status_code=404,
            detail=f"No results found for privacy request {privacy_request_id}",
        )

    return filtered_results


@router.get(
    PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_VIEW_DATA])],
    response_model=Optional[ManualWebhookData],
)
def view_uploaded_manual_webhook_data(
    *,
    connection_config: ConnectionConfig = Depends(_get_connection_config),
    privacy_request_id: str,
    db: Session = Depends(deps.get_db),
) -> Optional[ManualWebhookData]:
    """
    View uploaded data for this privacy request for the given access manual webhook

    If no data exists for this webhook, we just return all fields as None.
    If we have missing or extra fields saved, we'll just return the overlap between what is saved and what is defined on the webhook.

    If checked=False, data must be reviewed before submission. The privacy request should not be submitted as-is.
    """
    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db,
        privacy_request_id,
        error_if_deleted=False,
    )
    access_manual_webhook: AccessManualWebhook = get_access_manual_webhook_or_404(
        connection_config
    )

    if not privacy_request.status == PrivacyRequestStatus.requires_input:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid manual webhook access upload request: privacy request "
            f"'{privacy_request.id}' status = {privacy_request.status.value}.",  # type: ignore
        )

    try:
        logger.info(
            "Retrieving input data for access manual webhook '{}' for privacy request '{}'.",
            connection_config.key,
            privacy_request.id,
        )
        data: Dict[str, Any] = privacy_request.get_manual_webhook_access_input_strict(
            access_manual_webhook
        )
        checked = True
    except (
        PydanticValidationError,
        ManualWebhookFieldsUnset,
        NoCachedManualWebhookEntry,
    ) as exc:
        logger.info(exc)
        data = privacy_request.get_manual_webhook_access_input_non_strict(
            manual_webhook=access_manual_webhook
        )
        checked = False

    return ManualWebhookData(checked=checked, fields=data)


@router.get(
    PRIVACY_REQUEST_MANUAL_WEBHOOK_ERASURE_INPUT,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_VIEW_DATA])],
    response_model=Optional[ManualWebhookData],
)
def view_uploaded_erasure_manual_webhook_data(
    *,
    connection_config: ConnectionConfig = Depends(_get_connection_config),
    privacy_request_id: str,
    db: Session = Depends(deps.get_db),
) -> Optional[ManualWebhookData]:
    """
    View uploaded erasure data for this privacy request for the given manual webhook

    If no data exists for this webhook, we just return all fields as None.
    If we have missing or extra fields saved, we'll just return the overlap between what is saved and what is defined on the webhook.

    If checked=False, data must be reviewed before submission. The privacy request should not be submitted as-is.
    """
    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db,
        privacy_request_id,
        error_if_deleted=False,
    )
    manual_webhook: AccessManualWebhook = get_access_manual_webhook_or_404(
        connection_config
    )

    if not privacy_request.status == PrivacyRequestStatus.requires_input:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid manual webhook erasure upload request: privacy request "
            f"'{privacy_request.id}' status = {privacy_request.status.value}.",  # type: ignore
        )

    try:
        logger.info(
            "Retrieving erasure input data for manual webhook '{}' for privacy request '{}'.",
            connection_config.key,
            privacy_request.id,
        )
        data: Dict[str, Any] = privacy_request.get_manual_webhook_erasure_input_strict(
            manual_webhook
        )
        checked = True
    except (
        PydanticValidationError,
        ManualWebhookFieldsUnset,
        NoCachedManualWebhookEntry,
    ) as exc:
        logger.info(exc)
        data = privacy_request.get_manual_webhook_erasure_input_non_strict(
            manual_webhook=manual_webhook
        )
        checked = False

    return ManualWebhookData(checked=checked, fields=data)


@router.post(
    PRIVACY_REQUEST_RESUME_FROM_REQUIRES_INPUT,
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestResponse,
    dependencies=[
        Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
    ],
)
def resume_privacy_request_from_requires_input(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
) -> PrivacyRequestResponse:
    """Resume a privacy request from 'requires_input' status."""
    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id
    )

    if privacy_request.status != PrivacyRequestStatus.requires_input:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume privacy request from 'requires_input': privacy request '{privacy_request.id}' status = {privacy_request.status.value}.",
            # type: ignore
        )

    action_type = None
    if privacy_request.policy.get_rules_for_action(ActionType.access):
        action_type = ActionType.access
    elif privacy_request.policy.get_rules_for_action(ActionType.erasure):
        action_type = ActionType.erasure

    access_manual_webhooks: List[AccessManualWebhook] = AccessManualWebhook.get_enabled(
        db, action_type
    )
    try:
        for manual_webhook in access_manual_webhooks:
            # check the access or erasure cache based on the privacy request's action type
            if action_type == ActionType.access:
                privacy_request.get_manual_webhook_access_input_strict(manual_webhook)
            if action_type == ActionType.erasure:
                privacy_request.get_manual_webhook_erasure_input_strict(manual_webhook)
    except (
        NoCachedManualWebhookEntry,
        PydanticValidationError,
        ManualWebhookFieldsUnset,
    ) as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume privacy request. {exc}",
        )

    logger.info(
        "Resuming privacy request '{}' after manual inputs verified",
        privacy_request_id,
    )

    privacy_request.status = PrivacyRequestStatus.in_processing
    privacy_request.save(db=db)
    queue_privacy_request(
        privacy_request_id=privacy_request.id,
    )

    return privacy_request  # type: ignore[return-value]


@router.post(
    PRIVACY_REQUEST_BULK_FINALIZE,
    status_code=HTTP_200_OK,
    response_model=BulkReviewResponse,
)
def bulk_finalize_privacy_requests(
    privacy_requests: PrivacyRequestBulkSelection,
    *,
    db: Session = Depends(deps.get_db),
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[PRIVACY_REQUEST_REVIEW],
    ),
    privacy_request_service: PrivacyRequestService = Depends(
        get_privacy_request_service
    ),
) -> BulkReviewResponse:
    """
    Each request will be moved from the 'requires_finalization' state to 'complete'.
    Returns an object with the list of successfully finalized privacy requests and the list of failed finalizations.

    You can either provide explicit request_ids OR use filters to select privacy requests.
    When using filters, you can optionally exclude specific IDs via exclude_ids.

    For backwards compatibility, a plain list of request IDs is also accepted.
    """
    # Resolve request IDs from either explicit list or filters
    try:
        request_ids = privacy_request_service.resolve_request_ids(privacy_requests)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return privacy_request_service.finalize_privacy_requests(
        request_ids, user_id=client.user_id
    )


@router.post(
    PRIVACY_REQUEST_FINALIZE,
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestResponse,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_REVIEW])],
)
def finalize_privacy_request(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[PRIVACY_REQUEST_REVIEW],
    ),
) -> PrivacyRequestResponse:
    """
    Finalizes a privacy request, moving it from the 'requires_finalization' state to 'complete'.
    This is done by re-queueing the request, which will then hit the finalization logic in the
    request runner service. This logic marks the privacy request as complete
    and sends out any configured messaging to the user.
    """
    privacy_request = get_privacy_request_or_error(db, privacy_request_id)

    if privacy_request.status != PrivacyRequestStatus.requires_manual_finalization:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot manually finalize privacy request '{privacy_request_id}': status is {privacy_request.status}, not requires_manual_finalization.",
        )

    # Set finalized_by and finalized_at here, so the request runner service knows not to
    # put the request back into the requires_finalization state.
    privacy_request.finalized_at = datetime.now(timezone.utc)
    privacy_request.finalized_by = client.user_id
    privacy_request.save(db=db)

    queue_privacy_request(
        privacy_request_id=privacy_request_id,
        from_step=CurrentStep.finalization.value,
    )

    return privacy_request  # type: ignore[return-value]


@router.get(
    REQUEST_TASKS,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_READ])],
    response_model=List[PrivacyRequestTaskSchema],
)
def get_individual_privacy_request_tasks(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
) -> List[RequestTask]:
    """Returns individual Privacy Request Tasks created by DSR 3.0 scheduler
    in order by creation and collection address"""
    pr: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id, error_if_deleted=False
    )

    logger.info(f"Getting Request Tasks for '{privacy_request_id}'")

    # Use deferred loading to avoid loading large JSON columns (_access_data, _data_for_erasures, etc.)
    # which can cause OOM errors when listing many tasks
    return (
        RequestTask.query_with_deferred_data(db.query(RequestTask))
        .filter(RequestTask.privacy_request_id == privacy_request_id)
        .order_by(RequestTask.created_at.asc(), RequestTask.collection_address.asc())
        .all()
    )


@router.post(
    PRIVACY_REQUEST_REQUEUE,
    dependencies=[
        Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
    ],
    response_model=PrivacyRequestResponse,
)
def requeue_privacy_request(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
) -> PrivacyRequestResponse:
    """
    Endpoint for manually re-queuing a stuck Privacy Request from selected states - use with caution.

    Don't use this unless the Privacy Request is stuck.
    """
    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id
    )

    try:
        return _requeue_privacy_request(db, privacy_request)
    except PrivacyRequestError as exc:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )


@router.post(
    REQUEST_TASK_CALLBACK,
    response_model=Dict,
)
def request_task_async_callback(
    *,
    data: RequestTaskCallbackRequest,
    request_task: RequestTask = Security(
        verify_request_task_callback, scopes=[PRIVACY_REQUEST_CALLBACK_RESUME]
    ),
) -> Dict:
    """
    For DSR 3.0: Async Callback Endpoint for Request Tasks

    Re-queues Request Task with asynchronously-retrieved results.  If you don't want to supply results, hitting
    this endpoint with an empty json request body will be taken as verification the async or erasure request
    for this request task is complete.
    """
    db = Session.object_session(
        request_task
    )  # Use the session created in the jwe verification

    privacy_request: PrivacyRequest = request_task.privacy_request
    if privacy_request.status not in [
        PrivacyRequestStatus.in_processing,
        PrivacyRequestStatus.approved,
    ]:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Callback failed. Cannot queue {request_task.action_type} task '{request_task.id}' with privacy request status '{privacy_request.status.value}'",
        )
    if request_task.status != ExecutionLogStatus.awaiting_processing:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Callback failed. Cannot queue {request_task.action_type} task '{request_task.id}' with request task status '{request_task.status.value}'",
        )
    logger.info(
        "Callback received for {} task {} {}",
        request_task.action_type,
        request_task.collection_address,
        request_task.id,
    )
    # Mark that the callback was received on the task itself.
    request_task.callback_succeeded = True

    if data.access_results and request_task.action_type == ActionType.access:
        # If access data should be added to results package, it should be
        # supplied in request body as a list of rows.  This data will be further filtered
        # by the policy before uploading to the end user
        request_task.access_data = data.access_results or []
    if data.rows_masked and request_task.action_type == ActionType.erasure:
        # For erasure requests, rows masked can be supplied here.
        request_task.rows_masked = data.rows_masked

    request_task.update_status(db, ExecutionLogStatus.pending)
    request_task.save(db)

    log_task_queued(request_task, "callback")
    queue_request_task(request_task, privacy_request_proceed=True)

    return {"task_queued": True}


@router.post(
    PRIVACY_REQUEST_BULK_SOFT_DELETE,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_DELETE])],
    status_code=HTTP_200_OK,
    response_model=BulkSoftDeletePrivacyRequests,
)
def bulk_soft_delete_privacy_requests(
    privacy_requests: PrivacyRequestBulkSelection,
    *,
    db: Session = Depends(deps.get_db),
    privacy_request_service: PrivacyRequestService = Depends(
        get_privacy_request_service
    ),
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[PRIVACY_REQUEST_DELETE],
    ),
) -> BulkSoftDeletePrivacyRequests:
    """
    Soft delete a list of privacy requests. The requests' deleted_at field will be populated with the current datetime
    and its deleted_by field will be populated with the user_id of the user who initiated the deletion. Returns an
    object with the list of successfully deleted privacy requests and the list of failed deletions.

    You can either provide explicit request_ids OR use filters to select privacy requests.
    When using filters, you can optionally exclude specific IDs via exclude_ids.

    For backwards compatibility, a plain list of request IDs is also accepted.
    """
    succeeded: List[str] = []
    failed: List[Dict[str, Any]] = []

    user_id = client.user_id
    if client.id == CONFIG.security.oauth_root_client_id:
        user_id = "root"

    # Resolve request IDs from either explicit list or filters
    try:
        request_ids = privacy_request_service.resolve_request_ids(privacy_requests)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    batches = PrivacyRequestService.get_batches_for_bulk_operation(request_ids)

    # Process each batch to avoid memory issues with large request lists
    for batch in batches:
        # Fetch privacy requests for this batch in one query to avoid N+1
        privacy_requests_dict = {
            pr.id: pr
            for pr in PrivacyRequest.query_without_large_columns(db)
            .filter(PrivacyRequest.id.in_(batch))
            .all()
        }

        for privacy_request_id in batch:
            privacy_request = privacy_requests_dict.get(privacy_request_id)

            if not privacy_request:
                failed.append(
                    {
                        "message": f"No privacy request found with id '{privacy_request_id}'",
                        "data": {"privacy_request_id": privacy_request_id},
                    }
                )
                continue

            if privacy_request.deleted_at is not None:
                failed.append(
                    {
                        "message": f"Privacy request '{privacy_request_id}' has already been deleted.",
                        "data": {"privacy_request_id": privacy_request_id},
                    }
                )
                continue

            privacy_request.soft_delete(db, user_id)
            succeeded.append(privacy_request.id)

    return BulkSoftDeletePrivacyRequests(succeeded=succeeded, failed=failed)


@router.post(
    PRIVACY_REQUEST_SOFT_DELETE,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_DELETE])],
    status_code=HTTP_200_OK,
    response_model=None,
)
def soft_delete_privacy_request(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[PRIVACY_REQUEST_DELETE],
    ),
) -> None:
    """
    Endpoint for soft deleting a privacy request. The request's deleted_at field will be populated with the current datetime
    and its deleted_by field will be populated with the user_id of the user who initiated the deletion.
    """
    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id
    )
    user_id = client.user_id
    if client.id == CONFIG.security.oauth_root_client_id:
        user_id = "root"

    privacy_request.soft_delete(db, user_id)


@router.get(
    PRIVACY_REQUEST_ACCESS_RESULTS,
    dependencies=[
        Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_READ_ACCESS_RESULTS])
    ],
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestAccessResults,
)
def get_access_results_urls(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
) -> PrivacyRequestAccessResults:
    """
    Endpoint for retrieving access results URLs for a privacy request.
    """
    if not CONFIG.security.subject_request_download_ui_enabled:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Access results download is disabled.",
        )
    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id
    )

    if privacy_request.status != PrivacyRequestStatus.complete:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Access results for privacy request '{privacy_request_id}' are not available because the request is not complete.",
        )

    if not privacy_request.access_result_urls:
        return PrivacyRequestAccessResults(access_result_urls=[])

    return privacy_request.access_result_urls


@router.get(
    PRIVACY_REQUEST_FILTERED_RESULTS,
    dependencies=[
        Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_READ_ACCESS_RESULTS])
    ],
    status_code=HTTP_200_OK,
    response_model=FilteredPrivacyRequestResults,
)
def get_test_privacy_request_results(
    privacy_request_id: str,
    db: Session = Depends(deps.get_db),
) -> Dict[str, Any]:
    """Get filtered results for a test privacy request and update its status if complete."""
    privacy_request = get_privacy_request_or_error(db, privacy_request_id)

    if privacy_request.source != PrivacyRequestSource.dataset_test:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Results can only be retrieved for test privacy requests.",
        )

    # Check completion status of all tasks
    dataset_key, statuses = get_task_info(privacy_request.access_tasks.all())
    all_completed = all(status in EXITED_EXECUTION_LOG_STATUSES for status in statuses)

    # Update request status if all tasks are done
    if all_completed:
        has_errors = ExecutionLogStatus.error in statuses
        privacy_request.status = (
            PrivacyRequestStatus.error if has_errors else PrivacyRequestStatus.complete
        )
        privacy_request.save(db=db)

    # Escape datetime and ObjectId values
    raw_data = privacy_request.get_raw_access_results()
    escaped_json = json.dumps(raw_data, indent=2, cls=StorageJSONEncoder)
    results = json.loads(escaped_json)

    filtered_results: Dict[str, Any] = filter_access_results(
        db,
        results,
        dataset_key,
        privacy_request.policy_id,  # type: ignore[arg-type]
    )

    with logger.contextualize(
        privacy_request_id=privacy_request.id,
        privacy_request_source=privacy_request.source.value,
    ):
        logger.info("Privacy request run completed.")

        return {
            "privacy_request_id": privacy_request.id,
            "status": privacy_request.status,
            "results": (
                filtered_results
                if CONFIG.security.dsr_testing_tools_enabled
                else "DSR testing tools are not enabled, results will not be shown."
            ),
        }


@router.post(
    PRIVACY_REQUEST_RESUBMIT,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_CREATE])],
    response_model=PrivacyRequestResponse,
)
def resubmit_privacy_request(
    privacy_request_id: str,
    *,
    privacy_request_service: PrivacyRequestService = Depends(
        get_privacy_request_service
    ),
) -> PrivacyRequest:
    try:
        privacy_request = privacy_request_service.resubmit_privacy_request(
            privacy_request_id
        )
    except FidesopsException as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message
        )

    if not privacy_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Privacy request not found"
        )

    return privacy_request


def get_task_info(tasks: List[RequestTask]) -> Tuple[str, List[ExecutionLogStatus]]:
    """Returns first dataset and list of statuses from tasks"""
    statuses = []
    dataset_key = None

    for task in tasks:
        statuses.append(task.status)
        if dataset_key is None and task.dataset_name not in [
            "__ROOT__",
            "__TERMINATE__",
        ]:
            dataset_key = task.dataset_name

    return dataset_key, statuses  # type: ignore[return-value]


def filter_access_results(
    db: Session,
    access_results: Dict[str, Any],
    dataset_key: str,
    policy_id: str,
) -> Dict[str, List[Dict[str, Optional[Any]]]]:
    """Filter access results based on policy data categories.

    Args:
        access_results: Raw access results to filter
        dataset_key: Key of the dataset to get the data categories from
        policy_id: ID of the policy containing target data categories

    Returns:
        Filtered results containing only data matching policy target data categories
    """
    # Get dataset graph, we're assuming a 1-to-1 relationship between DatasetConfig and Dataset
    dataset_config = DatasetConfig.filter(
        db=db, conditions=(DatasetConfig.fides_key == dataset_key)
    ).first()
    if not dataset_config:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No dataset with fides_key '{dataset_key}'",
        )

    # Test privacy requests operate on one dataset at a time
    graph_dataset = dataset_config.get_graph()
    modified_graph_dataset = replace_references_with_identities(
        dataset_config.fides_key, graph_dataset
    )
    dataset_graph = DatasetGraph(modified_graph_dataset)

    # Get policy target categories
    policy = Policy.get_by(db, field="id", value=policy_id)
    if not policy:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No policy with ID '{policy_id}'",
        )

    target_categories: Set[str] = set()
    for rule in policy.get_rules_for_action(action_type=ActionType.access):
        for target in rule.targets:  # type: ignore[attr-defined]
            target_categories.add(target.data_category)

    return filter_data_categories(access_results, target_categories, dataset_graph)


@router.get(
    "/privacy-request/{privacy_request_id}/logs",
    dependencies=[
        Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_READ_ACCESS_RESULTS])
    ],
    status_code=HTTP_200_OK,
    response_model=List[LogEntry],
)
def get_test_privacy_request_logs(
    privacy_request_id: str,
    db: Session = Depends(deps.get_db),
) -> List[Dict[str, Any]]:
    """Get logs for a test privacy request."""
    privacy_request = get_privacy_request_or_error(db, privacy_request_id)

    if privacy_request.source != PrivacyRequestSource.dataset_test:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Logs can only be retrieved for test privacy requests.",
        )

    if not CONFIG.security.dsr_testing_tools_enabled:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="DSR testing tools are not enabled.",
        )

    # Get logs from Redis
    cache = get_cache()
    return cache.get_decoded_list(f"log_{privacy_request_id}") or []


@router.post(
    PRIVACY_REQUEST_BATCH_EMAIL_SEND,
    dependencies=[
        Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_EMAIL_INTEGRATIONS_SEND])
    ],
    status_code=HTTP_200_OK,
    response_model=ResponseWithMessage,
)
def send_batch_email_integrations(
    background_tasks: BackgroundTasks,
) -> ResponseWithMessage:
    """Send batch email integrations for a privacy request."""
    background_tasks.add_task(send_email_batch)

    return ResponseWithMessage(
        message="Email batch job started. This may take a few minutes to complete."
    )
