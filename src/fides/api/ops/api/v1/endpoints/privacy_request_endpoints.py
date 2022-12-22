# pylint: disable=too-many-branches,too-many-lines, too-many-statements

import csv
import io
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Set, Union

import sqlalchemy
from fastapi import Body, Depends, HTTPException, Security
from fastapi.params import Query as FastAPIQuery
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from pydantic import ValidationError as PydanticValidationError
from pydantic import conlist
from sqlalchemy import cast, column, null
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.expression import nullslast
from starlette.responses import StreamingResponse
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_424_FAILED_DEPENDENCY,
)

from fides.api.ops import common_exceptions
from fides.api.ops.api import deps
from fides.api.ops.api.v1.endpoints.dataset_endpoints import _get_connection_config
from fides.api.ops.api.v1.endpoints.manual_webhook_endpoints import (
    get_access_manual_webhook_or_404,
)
from fides.api.ops.api.v1.scope_registry import (
    PRIVACY_REQUEST_CALLBACK_RESUME,
    PRIVACY_REQUEST_CREATE,
    PRIVACY_REQUEST_NOTIFICATIONS_CREATE_OR_UPDATE,
    PRIVACY_REQUEST_NOTIFICATIONS_READ,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_REVIEW,
    PRIVACY_REQUEST_TRANSFER,
    PRIVACY_REQUEST_UPLOAD_DATA,
    PRIVACY_REQUEST_VIEW_DATA,
)
from fides.api.ops.api.v1.urn_registry import (
    PRIVACY_REQUEST_ACCESS_MANUAL_WEBHOOK_INPUT,
    PRIVACY_REQUEST_APPROVE,
    PRIVACY_REQUEST_AUTHENTICATED,
    PRIVACY_REQUEST_BULK_RETRY,
    PRIVACY_REQUEST_DENY,
    PRIVACY_REQUEST_MANUAL_ERASURE,
    PRIVACY_REQUEST_MANUAL_INPUT,
    PRIVACY_REQUEST_NOTIFICATIONS,
    PRIVACY_REQUEST_RESUME,
    PRIVACY_REQUEST_RESUME_FROM_REQUIRES_INPUT,
    PRIVACY_REQUEST_RETRY,
    PRIVACY_REQUEST_TRANSFER_TO_PARENT,
    PRIVACY_REQUEST_VERIFY_IDENTITY,
    PRIVACY_REQUESTS,
    REQUEST_PREVIEW,
    REQUEST_STATUS_LOGS,
    V1_URL_PREFIX,
)
from fides.api.ops.common_exceptions import (
    FunctionalityNotConfigured,
    IdentityNotFoundException,
    IdentityVerificationException,
    ManualWebhookFieldsUnset,
    MessageDispatchException,
    NoCachedManualWebhookEntry,
    PolicyNotFoundException,
    TraversalError,
    ValidationError,
)
from fides.api.ops.graph.config import CollectionAddress
from fides.api.ops.graph.graph import DatasetGraph, Node
from fides.api.ops.graph.traversal import Traversal
from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.models.manual_webhook import AccessManualWebhook
from fides.api.ops.models.policy import (
    ActionType,
    CurrentStep,
    Policy,
    PolicyPreWebhook,
    Rule,
)
from fides.api.ops.models.privacy_request import (
    CheckpointActionRequired,
    ExecutionLog,
    PrivacyRequest,
    PrivacyRequestNotifications,
    PrivacyRequestStatus,
    ProvidedIdentity,
    ProvidedIdentityType,
)
from fides.api.ops.schemas.dataset import (
    CollectionAddressResponse,
    DryRunDatasetResponse,
)
from fides.api.ops.schemas.external_https import PrivacyRequestResumeFormat
from fides.api.ops.schemas.messaging.messaging import (
    FidesopsMessage,
    MessagingActionType,
    RequestReceiptBodyParams,
    RequestReviewDenyBodyParams,
)
from fides.api.ops.schemas.privacy_request import (
    BulkPostPrivacyRequests,
    BulkReviewResponse,
    DenyPrivacyRequests,
    ExecutionLogDetailResponse,
    ManualWebhookData,
    PrivacyRequestCreate,
    PrivacyRequestNotificationInfo,
    PrivacyRequestResponse,
    PrivacyRequestVerboseResponse,
    ReviewPrivacyRequestIds,
    RowCountRequest,
    VerificationCode,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service._verification import send_verification_code_to_user
from fides.api.ops.service.messaging.message_dispatch_service import (
    EMAIL_JOIN_STRING,
    check_and_dispatch_error_notifications,
    dispatch_message_task,
)
from fides.api.ops.service.privacy_request.request_runner_service import (
    queue_privacy_request,
)
from fides.api.ops.service.privacy_request.request_service import (
    build_required_privacy_request_kwargs,
    cache_data,
)
from fides.api.ops.task.filter_results import filter_data_categories
from fides.api.ops.task.graph_task import EMPTY_REQUEST, collect_queries
from fides.api.ops.task.task_resources import TaskResources
from fides.api.ops.tasks import MESSAGING_QUEUE_NAME
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.cache import FidesopsRedis
from fides.api.ops.util.collection_util import Row
from fides.api.ops.util.enums import ColumnSort
from fides.api.ops.util.logger import Pii
from fides.api.ops.util.oauth_util import verify_callback_oauth, verify_oauth_client
from fides.core.config import get_config
from fides.lib.models.audit_log import AuditLog, AuditLogAction
from fides.lib.models.client import ClientDetail

router = APIRouter(tags=["Privacy Requests"], prefix=V1_URL_PREFIX)
CONFIG = get_config()
EMBEDDED_EXECUTION_LOG_LIMIT = 50


def get_privacy_request_or_error(
    db: Session, privacy_request_id: str
) -> PrivacyRequest:
    """Load the privacy request or throw a 404"""
    logger.info("Finding privacy request with id '{}'", privacy_request_id)

    privacy_request = PrivacyRequest.get(db, object_id=privacy_request_id)

    if not privacy_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No privacy request found with id '{privacy_request_id}'.",
        )

    return privacy_request


@router.post(
    PRIVACY_REQUESTS,
    status_code=HTTP_200_OK,
    response_model=BulkPostPrivacyRequests,
)
def create_privacy_request(
    *,
    db: Session = Depends(deps.get_db),
    data: conlist(PrivacyRequestCreate, max_items=50) = Body(...),  # type: ignore
) -> BulkPostPrivacyRequests:
    """
    Given a list of privacy request data elements, create corresponding PrivacyRequest objects
    or report failure and execute them within the Fidesops system.
    You cannot update privacy requests after they've been created.
    """
    return _create_privacy_request(db, data, False)


@router.post(
    PRIVACY_REQUEST_AUTHENTICATED,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_CREATE])],
    response_model=BulkPostPrivacyRequests,
)
def create_privacy_request_authenticated(
    *,
    db: Session = Depends(deps.get_db),
    data: conlist(PrivacyRequestCreate, max_items=50) = Body(...),  # type: ignore
) -> BulkPostPrivacyRequests:
    """
    Given a list of privacy request data elements, create corresponding PrivacyRequest objects
    or report failure and execute them within the Fidesops system.
    You cannot update privacy requests after they've been created.
    This route requires authentication instead of using verification codes.
    """
    return _create_privacy_request(db, data, True)


def _send_privacy_request_receipt_message_to_user(
    policy: Optional[Policy], to_identity: Optional[Identity]
) -> None:
    """Helper function to send request receipt message to the user"""
    if not to_identity:
        logger.error(
            IdentityNotFoundException(
                "Identity was not found, so request receipt message could not be sent."
            )
        )
        return
    if not policy:
        logger.error(
            PolicyNotFoundException(
                "Policy was not found, so request receipt message could not be sent."
            )
        )
        return
    request_types: Set[str] = set()
    for action_type in ActionType:
        if policy.get_rules_for_action(action_type=ActionType(action_type)):
            request_types.add(action_type)
    dispatch_message_task.apply_async(
        queue=MESSAGING_QUEUE_NAME,
        kwargs={
            "message_meta": FidesopsMessage(
                action_type=MessagingActionType.PRIVACY_REQUEST_RECEIPT,
                body_params=RequestReceiptBodyParams(request_types=request_types),
            ).dict(),
            "service_type": CONFIG.notifications.notification_service_type,
            "to_identity": to_identity.dict(),
        },
    )


def privacy_request_csv_download(
    db: Session, privacy_request_query: Query
) -> StreamingResponse:
    """Download privacy requests as CSV for Admin UI"""
    f = io.StringIO()
    csv_file = csv.writer(f)

    csv_file.writerow(
        [
            "Time received",
            "Subject identity",
            "Policy key",
            "Request status",
            "Reviewer",
            "Time approved/denied",
            "Denial reason",
        ]
    )
    privacy_request_ids: List[str] = [r.id for r in privacy_request_query]
    denial_audit_log_query: Query = db.query(AuditLog).filter(
        AuditLog.action == AuditLogAction.denied,
        AuditLog.privacy_request_id.in_(privacy_request_ids),
    )
    denial_audit_logs: Dict[str, str] = {
        r.privacy_request_id: r.message for r in denial_audit_log_query
    }

    for pr in privacy_request_query:
        denial_reason = (
            denial_audit_logs[pr.id]
            if pr.status == PrivacyRequestStatus.denied and pr.id in denial_audit_logs
            else None
        )
        csv_file.writerow(
            [
                pr.created_at,
                pr.get_persisted_identity().dict(),
                pr.policy.key if pr.policy else None,
                pr.status.value if pr.status else None,
                pr.reviewed_by,
                pr.reviewed_at,
                denial_reason,
            ]
        )
    f.seek(0)
    response = StreamingResponse(f, media_type="text/csv")
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename=privacy_requests_download_{datetime.today().strftime('%Y-%m-%d')}.csv"
    return response


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
        cast(ExecutionLog.status, sqlalchemy.String).label("status"),
        ExecutionLog.privacy_request_id,
        ExecutionLog.dataset_name,
        ExecutionLog.collection_name,
        ExecutionLog.fields_affected,
        ExecutionLog.action_type,
        null().label("user_id"),
    ).filter(ExecutionLog.privacy_request_id == self.id)

    audit_log_query: Query = db.query(
        AuditLog.id,
        AuditLog.created_at,
        AuditLog.updated_at,
        AuditLog.message,
        cast(AuditLog.action.label("status"), sqlalchemy.String).label("status"),
        AuditLog.privacy_request_id,
        null().label("dataset_name"),
        null().label("collection_name"),
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


def _filter_privacy_request_queryset(
    db: Session,
    query: Query,
    request_id: Optional[str] = None,
    identity: Optional[str] = None,
    status: Optional[List[PrivacyRequestStatus]] = None,
    created_lt: Optional[datetime] = None,
    created_gt: Optional[datetime] = None,
    started_lt: Optional[datetime] = None,
    started_gt: Optional[datetime] = None,
    completed_lt: Optional[datetime] = None,
    completed_gt: Optional[datetime] = None,
    errored_lt: Optional[datetime] = None,
    errored_gt: Optional[datetime] = None,
    external_id: Optional[str] = None,
) -> Query:
    """
    Utility method to apply filters to our privacy request query.

    Status supports "or" filtering:
    ?status=approved&status=pending will be translated into an "or" query.
    """
    if any([completed_lt, completed_gt]) and any([errored_lt, errored_gt]):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Cannot specify both succeeded and failed query params.",
        )

    for end, start, field_name in [
        [created_lt, created_gt, "created"],
        [completed_lt, completed_gt, "completed"],
        [errored_lt, errored_gt, "errored"],
        [started_lt, started_gt, "started"],
    ]:
        if end is None or start is None:
            continue

        if not (isinstance(end, datetime) and isinstance(start, datetime)):
            continue

        if end < start:
            # With date fields, if the start date is after the end date, return a 400
            # because no records will lie within this range.
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Value specified for {field_name}_lt: {end} must be after {field_name}_gt: {start}.",
            )

    if identity:
        hashed_identity = ProvidedIdentity.hash_value(value=identity)
        identities: Set[str] = {
            identity[0]
            for identity in ProvidedIdentity.filter(
                db=db,
                conditions=(
                    (ProvidedIdentity.hashed_value == hashed_identity)
                    & (ProvidedIdentity.privacy_request_id.isnot(None))
                ),
            ).values(column("privacy_request_id"))
        }
        query = query.filter(PrivacyRequest.id.in_(identities))
    # Further restrict all PrivacyRequests by query params
    if request_id:
        query = query.filter(PrivacyRequest.id.ilike(f"{request_id}%"))
    if external_id:
        query = query.filter(PrivacyRequest.external_id.ilike(f"{external_id}%"))
    if status:
        query = query.filter(PrivacyRequest.status.in_(status))
    if created_lt:
        query = query.filter(PrivacyRequest.created_at < created_lt)
    if created_gt:
        query = query.filter(PrivacyRequest.created_at > created_gt)
    if started_lt:
        query = query.filter(PrivacyRequest.started_processing_at < started_lt)
    if started_gt:
        query = query.filter(PrivacyRequest.started_processing_at > started_gt)
    if completed_lt:
        query = query.filter(
            PrivacyRequest.status == PrivacyRequestStatus.complete,
            PrivacyRequest.finished_processing_at < completed_lt,
        )
    if completed_gt:
        query = query.filter(
            PrivacyRequest.status == PrivacyRequestStatus.complete,
            PrivacyRequest.finished_processing_at > completed_gt,
        )
    if errored_lt:
        query = query.filter(
            PrivacyRequest.status == PrivacyRequestStatus.error,
            PrivacyRequest.finished_processing_at < errored_lt,
        )
    if errored_gt:
        query = query.filter(
            PrivacyRequest.status == PrivacyRequestStatus.error,
            PrivacyRequest.finished_processing_at > errored_gt,
        )

    return query


def _sort_privacy_request_queryset(
    query: Query, sort_field: str, sort_direction: ColumnSort
) -> Query:
    if hasattr(PrivacyRequest, sort_field) is False:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{sort_field} is not on PrivacyRequest",
        )

    sort_object_attribute = getattr(PrivacyRequest, sort_field)
    sort_func = getattr(sort_object_attribute, sort_direction)
    return query.order_by(nullslast(sort_func()))


def attach_resume_instructions(privacy_request: PrivacyRequest) -> None:
    """
    Temporarily update a paused/errored/requires_input privacy request object with instructions from the Redis cache
    about how to resume manually if applicable.
    """
    resume_endpoint: Optional[str] = None
    action_required_details: Optional[CheckpointActionRequired] = None

    if privacy_request.status == PrivacyRequestStatus.paused:
        action_required_details = privacy_request.get_paused_collection_details()

        if action_required_details:
            # Graph is paused on a specific collection
            resume_endpoint = (
                PRIVACY_REQUEST_MANUAL_ERASURE
                if action_required_details.step == CurrentStep.erasure
                else PRIVACY_REQUEST_MANUAL_INPUT
            )
        else:
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
            action_required_details.collection.value if action_required_details.collection else None  # type: ignore
        )

    privacy_request.action_required_details = action_required_details
    # replaces the placeholder in the url with the privacy request id
    privacy_request.resume_endpoint = (
        resume_endpoint.format(privacy_request_id=privacy_request.id)
        if resume_endpoint
        else None
    )


@router.get(
    PRIVACY_REQUESTS,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_READ])],
    response_model=Page[
        Union[
            PrivacyRequestVerboseResponse,
            PrivacyRequestResponse,
        ]
    ],
)
def get_request_status(
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    request_id: Optional[str] = None,
    identity: Optional[str] = None,
    status: Optional[List[PrivacyRequestStatus]] = FastAPIQuery(
        default=None
    ),  # type:ignore
    created_lt: Optional[datetime] = None,
    created_gt: Optional[datetime] = None,
    started_lt: Optional[datetime] = None,
    started_gt: Optional[datetime] = None,
    completed_lt: Optional[datetime] = None,
    completed_gt: Optional[datetime] = None,
    errored_lt: Optional[datetime] = None,
    errored_gt: Optional[datetime] = None,
    external_id: Optional[str] = None,
    verbose: Optional[bool] = False,
    include_identities: Optional[bool] = False,
    download_csv: Optional[bool] = False,
    sort_field: str = "created_at",
    sort_direction: ColumnSort = ColumnSort.DESC,
) -> Union[StreamingResponse, AbstractPage[PrivacyRequest]]:
    """Returns PrivacyRequest information. Supports a variety of optional query params.

    To fetch a single privacy request, use the request_id query param `?request_id=`.
    To see individual execution logs, use the verbose query param `?verbose=True`.
    """
    logger.info("Finding all request statuses with pagination params {}", params)

    query = db.query(PrivacyRequest)
    query = _filter_privacy_request_queryset(
        db,
        query,
        request_id,
        identity,
        status,
        created_lt,
        created_gt,
        started_lt,
        started_gt,
        completed_lt,
        completed_gt,
        errored_lt,
        errored_gt,
        external_id,
    )

    logger.info(
        "Sorting requests by field: {} and direction: {}", sort_field, sort_direction
    )
    query = _sort_privacy_request_queryset(query, sort_field, sort_direction)

    if download_csv:
        # Returning here if download_csv param was specified
        logger.info("Downloading privacy requests as csv")
        return privacy_request_csv_download(db, query)

    # Conditionally embed execution log details in the response.
    if verbose:
        logger.info("Finding execution and audit log details")
        PrivacyRequest.execution_and_audit_logs_by_dataset = property(
            execution_and_audit_logs_by_dataset_name
        )
    else:
        PrivacyRequest.execution_and_audit_logs_by_dataset = property(lambda self: None)

    paginated = paginate(query, params)
    if include_identities:
        # Conditionally include the cached identity data in the response if
        # it is explicitly requested
        for item in paginated.items:  # type: ignore
            item.identity = item.get_persisted_identity().dict()
            attach_resume_instructions(item)
    else:
        for item in paginated.items:  # type: ignore
            attach_resume_instructions(item)

    return paginated


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

    get_privacy_request_or_error(db, privacy_request_id)

    logger.info(
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
        info = PrivacyRequestNotifications.all(db)
        if info:
            info[0].delete(db)
        return PrivacyRequestNotificationInfo(
            email_addresses=[],
            notify_after_failures=request_body.notify_after_failures,
        )

    notification_info = {
        "email": EMAIL_JOIN_STRING.join(request_body.email_addresses),
        "notify_after_failures": request_body.notify_after_failures,
    }
    info_check = PrivacyRequestNotifications.all(db)
    if info_check:
        info = info_check[0].update(db=db, data=notification_info)
        return PrivacyRequestNotificationInfo(
            email_addresses=info.email.split(", "),
            notify_after_failures=info.notify_after_failures,
        )

    info = PrivacyRequestNotifications.create(db=db, data=notification_info)
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
        connection_configs: List[ConnectionConfig] = [
            ConnectionConfig.get(db=db, object_id=dataset.connection_config_id)
            for dataset in dataset_configs
        ]

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
            TaskResources(EMPTY_REQUEST, Policy(), connection_configs, db),
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
        verify_callback_oauth, scopes=[PRIVACY_REQUEST_CALLBACK_RESUME]
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
            detail=f"Invalid resume request: privacy request '{privacy_request.id}' status = {privacy_request.status.value}.",  # type: ignore
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
    return privacy_request


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
            if not dataset_graph.nodes[collection].contains_field(
                lambda f: f.name == field_name  # pylint: disable=W0640
            ):
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Cannot save manual rows. No '{field_name}' field defined on the '{collection.value}' collection.",
                )


def resume_privacy_request_with_manual_input(
    privacy_request_id: str,
    db: Session,
    expected_paused_step: CurrentStep,
    manual_rows: List[Row] = [],
    manual_count: Optional[int] = None,
) -> PrivacyRequest:
    """Resume privacy request after validating and caching manual data for an access or an erasure request.

    This assumes the privacy request is being resumed from a specific collection in the graph.
    """
    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id
    )
    if privacy_request.status != PrivacyRequestStatus.paused:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid resume request: privacy request '{privacy_request.id}' "  # type: ignore
            f"status = {privacy_request.status.value}. Privacy request is not paused.",
        )

    paused_details: Optional[
        CheckpointActionRequired
    ] = privacy_request.get_paused_collection_details()
    if not paused_details:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume privacy request '{privacy_request.id}'; no paused details.",
        )

    paused_step: CurrentStep = paused_details.step
    paused_collection: Optional[CollectionAddress] = paused_details.collection

    if paused_step != expected_paused_step:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Collection '{paused_collection}' is paused at the {paused_step.value} step. Pass in manual data instead to "
            f"'{PRIVACY_REQUEST_MANUAL_ERASURE if paused_step == CurrentStep.erasure else PRIVACY_REQUEST_MANUAL_INPUT}' to resume.",
        )

    datasets = DatasetConfig.all(db=db)
    dataset_graphs = [dataset_config.get_graph() for dataset_config in datasets]
    dataset_graph = DatasetGraph(*dataset_graphs)

    if not paused_collection:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot save manual data on paused collection. No paused collection saved'.",
        )

    node: Optional[Node] = dataset_graph.nodes.get(paused_collection)
    if not node:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot save manual data. No collection in graph with name: '{paused_collection.value}'.",
        )

    if paused_step == CurrentStep.access:
        validate_manual_input(manual_rows, paused_collection, dataset_graph)
        logger.info(
            "Caching manual input for privacy request '{}', collection: '{}'",
            privacy_request_id,
            paused_collection,
        )
        privacy_request.cache_manual_input(paused_collection, manual_rows)

    elif paused_step == CurrentStep.erasure:
        logger.info(
            "Caching manually erased row count for privacy request '{}', collection: '{}'",
            privacy_request_id,
            paused_collection,
        )
        privacy_request.cache_manual_erasure_count(paused_collection, manual_count)  # type: ignore

    logger.info(
        "Resuming privacy request '{}', {} step, from collection '{}'",
        privacy_request_id,
        paused_step.value,
        paused_collection.value,
    )

    privacy_request.status = PrivacyRequestStatus.in_processing
    privacy_request.save(db=db)

    queue_privacy_request(
        privacy_request_id=privacy_request.id,
        from_step=paused_step.value,
    )

    return privacy_request


@router.post(
    PRIVACY_REQUEST_MANUAL_INPUT,
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestResponse,
    dependencies=[
        Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
    ],
)
def resume_with_manual_input(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
    manual_rows: List[Row],
) -> PrivacyRequestResponse:
    """Resume a privacy request by passing in manual input for the paused collection.

    If there's no manual data to submit, pass in an empty list to resume the privacy request.
    """
    return resume_privacy_request_with_manual_input(
        privacy_request_id=privacy_request_id,
        db=db,
        expected_paused_step=CurrentStep.access,
        manual_rows=manual_rows,
    )


@router.post(
    PRIVACY_REQUEST_MANUAL_ERASURE,
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestResponse,
    dependencies=[
        Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_CALLBACK_RESUME])
    ],
)
def resume_with_erasure_confirmation(
    privacy_request_id: str,
    *,
    db: Session = Depends(deps.get_db),
    cache: FidesopsRedis = Depends(deps.get_cache),
    manual_count: RowCountRequest,
) -> PrivacyRequestResponse:
    """Resume the erasure portion of privacy request by passing in the number of rows that were manually masked.

    If no rows were masked, pass in a 0 to resume the privacy request.
    """
    return resume_privacy_request_with_manual_input(
        privacy_request_id=privacy_request_id,
        db=db,
        expected_paused_step=CurrentStep.erasure,
        manual_count=manual_count.row_count,
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
    privacy_request_ids: List[str],
    *,
    db: Session = Depends(deps.get_db),
) -> BulkPostPrivacyRequests:
    """Bulk restart a of privacy request from failure."""

    succeeded: List[PrivacyRequestResponse] = []
    failed: List[Dict[str, Any]] = []

    #    privacy_request = PrivacyRequest.get(db, object_id=request_id)

    for privacy_request_id in privacy_request_ids:
        privacy_request = PrivacyRequest.get(db, object_id=privacy_request_id)

        if not privacy_request:
            failed.append(
                {
                    "message": f"No privacy request found with id '{privacy_request_id}'",
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

        failed_details: Optional[
            CheckpointActionRequired
        ] = privacy_request.get_failed_checkpoint_details()
        if not failed_details:
            failed.append(
                {
                    "message": f"Cannot restart privacy request from failure '{privacy_request.id}'; no failed step or collection.",
                    "data": {"privacy_request_id": privacy_request_id},
                }
            )
            continue

        succeeded.append(
            _process_privacy_request_restart(
                privacy_request, failed_details.step, failed_details.collection, db
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
) -> PrivacyRequestResponse:
    """Restart a privacy request from failure"""
    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id
    )

    if privacy_request.status != PrivacyRequestStatus.error:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot restart privacy request from failure: privacy request '{privacy_request.id}' status = {privacy_request.status.value}.",  # type: ignore
        )

    failed_details: Optional[
        CheckpointActionRequired
    ] = privacy_request.get_failed_checkpoint_details()
    if not failed_details:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot restart privacy request from failure '{privacy_request.id}'; no failed step or collection.",
        )

    return _process_privacy_request_restart(
        privacy_request, failed_details.step, failed_details.collection, db
    )


def review_privacy_request(
    db: Session,
    request_ids: List[str],
    process_request_function: Callable,
) -> BulkReviewResponse:
    """Helper method shared between the approve and deny privacy request endpoints"""
    succeeded: List[PrivacyRequest] = []
    failed: List[Dict[str, Any]] = []

    for request_id in request_ids:
        privacy_request = PrivacyRequest.get(db, object_id=request_id)
        if not privacy_request:
            failed.append(
                {
                    "message": f"No privacy request found with id '{request_id}'",
                    "data": {"privacy_request_id": request_id},
                }
            )
            continue

        if privacy_request.status != PrivacyRequestStatus.pending:
            failed.append(
                {
                    "message": "Cannot transition status",
                    "data": PrivacyRequestResponse.from_orm(privacy_request),
                }
            )
            continue

        try:
            process_request_function(privacy_request)
        except Exception:
            failure = {
                "message": "Privacy request could not be updated",
                "data": PrivacyRequestResponse.from_orm(privacy_request),
            }
            failed.append(failure)
        else:
            succeeded.append(privacy_request)

    return BulkReviewResponse(
        succeeded=succeeded,
        failed=failed,
    )


def _send_privacy_request_review_message_to_user(
    action_type: MessagingActionType,
    identity_data: Dict[str, Any],
    rejection_reason: Optional[str],
) -> None:
    """Helper method to send review notification message to user, shared between approve and deny"""
    if not identity_data:
        logger.error(
            IdentityNotFoundException(
                "Identity was not found, so request review message could not be sent."
            )
        )
    to_identity: Identity = Identity(
        email=identity_data.get(ProvidedIdentityType.email.value),
        phone_number=identity_data.get(ProvidedIdentityType.phone_number.value),
    )
    dispatch_message_task.apply_async(
        queue=MESSAGING_QUEUE_NAME,
        kwargs={
            "message_meta": FidesopsMessage(
                action_type=action_type,
                body_params=RequestReviewDenyBodyParams(
                    rejection_reason=rejection_reason
                )
                if action_type is MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY
                else None,
            ).dict(),
            "service_type": CONFIG.notifications.notification_service_type,
            "to_identity": to_identity.dict(),
        },
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
    provided_code: VerificationCode,
) -> PrivacyRequestResponse:
    """Verify the supplied identity verification code.

    If successful, and we don't need separate manual request approval, queue the privacy request
    for execution.
    """

    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id
    )
    try:
        privacy_request.verify_identity(db, provided_code.code)
        policy: Optional[Policy] = Policy.get(
            db=db, object_id=privacy_request.policy_id
        )
        if CONFIG.notifications.send_request_receipt_notification:
            _send_privacy_request_receipt_message_to_user(
                policy, privacy_request.get_persisted_identity()
            )
    except IdentityVerificationException as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=exc.message)
    except PermissionError as exc:
        logger.info("Invalid verification code provided for {}.", privacy_request.id)
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=exc.args[0])

    logger.info("Identity verified for {}.", privacy_request.id)

    if not CONFIG.execution.require_manual_request_approval:
        AuditLog.create(
            db=db,
            data={
                "user_id": "system",
                "privacy_request_id": privacy_request.id,
                "action": AuditLogAction.approved,
                "message": "",
            },
        )
        queue_privacy_request(privacy_request.id)

    return privacy_request


@router.patch(
    PRIVACY_REQUEST_APPROVE,
    status_code=HTTP_200_OK,
    response_model=BulkReviewResponse,
)
def approve_privacy_request(
    *,
    db: Session = Depends(deps.get_db),
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[PRIVACY_REQUEST_REVIEW],
    ),
    privacy_requests: ReviewPrivacyRequestIds,
) -> BulkReviewResponse:
    """Approve and dispatch a list of privacy requests and/or report failure"""
    user_id = client.user_id

    def _approve_request(privacy_request: PrivacyRequest) -> None:
        """Method for how to process requests - approved"""
        privacy_request.status = PrivacyRequestStatus.approved
        privacy_request.reviewed_at = datetime.utcnow()
        privacy_request.reviewed_by = user_id
        privacy_request.save(db=db)
        AuditLog.create(
            db=db,
            data={
                "user_id": user_id,
                "privacy_request_id": privacy_request.id,
                "action": AuditLogAction.approved,
                "message": "",
            },
        )
        if CONFIG.notifications.send_request_review_notification:
            _send_privacy_request_review_message_to_user(
                action_type=MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE,
                identity_data=privacy_request.get_cached_identity_data(),
                rejection_reason=None,
            )

        queue_privacy_request(privacy_request_id=privacy_request.id)

    return review_privacy_request(
        db=db,
        request_ids=privacy_requests.request_ids,
        process_request_function=_approve_request,
    )


@router.patch(
    PRIVACY_REQUEST_DENY,
    status_code=HTTP_200_OK,
    response_model=BulkReviewResponse,
)
def deny_privacy_request(
    *,
    db: Session = Depends(deps.get_db),
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[PRIVACY_REQUEST_REVIEW],
    ),
    privacy_requests: DenyPrivacyRequests,
) -> BulkReviewResponse:
    """Deny a list of privacy requests and/or report failure"""
    user_id = client.user_id

    def _deny_request(
        privacy_request: PrivacyRequest,
    ) -> None:
        """Method for how to process requests - denied"""
        privacy_request.status = PrivacyRequestStatus.denied
        privacy_request.reviewed_at = datetime.utcnow()
        privacy_request.reviewed_by = user_id
        privacy_request.save(db=db)
        AuditLog.create(
            db=db,
            data={
                "user_id": user_id,
                "privacy_request_id": privacy_request.id,
                "action": AuditLogAction.denied,
                "message": privacy_requests.reason,
            },
        )
        if CONFIG.notifications.send_request_review_notification:
            _send_privacy_request_review_message_to_user(
                action_type=MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY,
                identity_data=privacy_request.get_cached_identity_data(),
                rejection_reason=privacy_requests.reason,
            )

    return review_privacy_request(
        db=db,
        request_ids=privacy_requests.request_ids,
        process_request_function=_deny_request,
    )


@router.patch(
    PRIVACY_REQUEST_ACCESS_MANUAL_WEBHOOK_INPUT,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_UPLOAD_DATA])],
    response_model=None,
)
def upload_manual_webhook_data(
    *,
    connection_config: ConnectionConfig = Depends(_get_connection_config),
    privacy_request_id: str,
    db: Session = Depends(deps.get_db),
    input_data: Dict[str, Any],
) -> None:
    """Upload manual input for the privacy request for the fields defined on the access manual webhook.
    The data collected here is not included in the graph but uploaded directly to the user at the end
    of privacy request execution.

    Because a 'manual_webhook' ConnectionConfig has one AccessManualWebhook associated with it,
    we are using the ConnectionConfig key as the AccessManualWebhook identifier here.
    """
    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id
    )
    access_manual_webhook: AccessManualWebhook = get_access_manual_webhook_or_404(
        connection_config
    )

    if not privacy_request.status == PrivacyRequestStatus.requires_input:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid access manual webhook upload request: privacy request '{privacy_request.id}' status = {privacy_request.status.value}.",  # type: ignore
        )

    try:
        privacy_request.cache_manual_webhook_input(access_manual_webhook, input_data)
    except PydanticValidationError as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()
        )

    logger.info(
        "Input saved for access manual webhook '{}' for privacy_request '{}'.",
        access_manual_webhook,
        privacy_request,
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
    """Transfer access request iinformation to the parent server."""
    privacy_request = PrivacyRequest.get(db=db, object_id=privacy_request_id)

    if not privacy_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No privacy request with id {privacy_request_id} found",
        )

    rule = Rule.filter(db=db, conditions=(Rule.key == rule_key)).first()
    if not rule:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Rule key {rule_key} not found",
        )

    value_dict: Dict[str, Optional[List[Row]]] = cache.get_encoded_objects_by_prefix(
        f"{privacy_request_id}__access_request"
    )

    if not value_dict:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No access request information found for privacy request id {privacy_request_id}",
        )

    access_result = {k.split("__")[-1]: v for k, v in value_dict.items()}
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
        dataset_graph.data_category_field_mapping,
    )

    if filtered_results is None:
        raise HTTPException(
            status_code=404,
            detail=f"No results found for privacy request {privacy_request_id}",
        )

    return filtered_results


@router.get(
    PRIVACY_REQUEST_ACCESS_MANUAL_WEBHOOK_INPUT,
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
        db, privacy_request_id
    )
    access_manual_webhook: AccessManualWebhook = get_access_manual_webhook_or_404(
        connection_config
    )

    if not privacy_request.status == PrivacyRequestStatus.requires_input:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid access manual webhook upload request: privacy request "
            f"'{privacy_request.id}' status = {privacy_request.status.value}.",  # type: ignore
        )

    try:
        logger.info(
            "Retrieving input data for access manual webhook '{}' for privacy request '{}'.",
            connection_config.key,
            privacy_request.id,
        )
        data: Dict[str, Any] = privacy_request.get_manual_webhook_input_strict(
            access_manual_webhook
        )
        checked = True
    except (
        PydanticValidationError,
        ManualWebhookFieldsUnset,
        NoCachedManualWebhookEntry,
    ) as exc:
        logger.info(exc)
        data = privacy_request.get_manual_webhook_input_non_strict(
            manual_webhook=access_manual_webhook
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
            detail=f"Cannot resume privacy request from 'requires_input': privacy request '{privacy_request.id}' status = {privacy_request.status.value}.",  # type: ignore
        )

    access_manual_webhooks: List[AccessManualWebhook] = AccessManualWebhook.get_enabled(
        db
    )
    try:
        for manual_webhook in access_manual_webhooks:
            privacy_request.get_manual_webhook_input_strict(manual_webhook)
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

    return privacy_request


def _create_privacy_request(
    db: Session,
    data: conlist(PrivacyRequestCreate),  # type: ignore
    authenticated: bool = False,
) -> BulkPostPrivacyRequests:
    """Creates privacy requests.

    If authenticated is True the identity verification step is bypassed.
    """
    if not CONFIG.redis.enabled:
        raise FunctionalityNotConfigured(
            "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a redis cache."
        )

    created = []
    failed = []
    # Optional fields to validate here are those that are both nullable in the DB, and exist
    # on the Pydantic schema

    logger.info("Starting creation for {} privacy requests", len(data))

    optional_fields = ["external_id", "started_processing_at", "finished_processing_at"]
    for privacy_request_data in data:
        if not any(privacy_request_data.identity.dict().values()):
            logger.warning(
                "Create failed for privacy request with no identity provided"
            )
            failure = {
                "message": "You must provide at least one identity to process",
                "data": privacy_request_data,
            }
            failed.append(failure)
            continue

        logger.info("Finding policy with key '{}'", privacy_request_data.policy_key)
        policy: Optional[Policy] = Policy.get_by(
            db=db,
            field="key",
            value=privacy_request_data.policy_key,
        )
        if policy is None:
            logger.warning(
                "Create failed for privacy request with invalid policy key {}'",
                privacy_request_data.policy_key,
            )

            failure = {
                "message": f"Policy with key {privacy_request_data.policy_key} does not exist",
                "data": privacy_request_data,
            }
            failed.append(failure)
            continue

        kwargs = build_required_privacy_request_kwargs(
            privacy_request_data.requested_at, policy.id
        )
        for field in optional_fields:
            attr = getattr(privacy_request_data, field)
            if attr is not None:
                kwargs[field] = attr

        try:
            privacy_request: PrivacyRequest = PrivacyRequest.create(db=db, data=kwargs)
            privacy_request.persist_identity(
                db=db, identity=privacy_request_data.identity
            )

            cache_data(
                privacy_request,
                policy,
                privacy_request_data.identity,
                privacy_request_data.encryption_key,
                None,
            )

            check_and_dispatch_error_notifications(db=db)

            if (
                not authenticated
                and CONFIG.execution.subject_identity_verification_required
            ):
                send_verification_code_to_user(
                    db, privacy_request, privacy_request_data.identity
                )
                created.append(privacy_request)
                continue  # Skip further processing for this privacy request
            if (
                not authenticated
                and CONFIG.notifications.send_request_receipt_notification
            ):
                _send_privacy_request_receipt_message_to_user(
                    policy, privacy_request_data.identity
                )
            if not CONFIG.execution.require_manual_request_approval:
                AuditLog.create(
                    db=db,
                    data={
                        "user_id": "system",
                        "privacy_request_id": privacy_request.id,
                        "action": AuditLogAction.approved,
                        "message": "",
                    },
                )
                queue_privacy_request(privacy_request.id)
        except MessageDispatchException as exc:
            kwargs["privacy_request_id"] = privacy_request.id
            logger.error("MessageDispatchException: {}", exc)
            failure = {
                "message": "Verification message could not be sent.",
                "data": kwargs,
            }
            failed.append(failure)
        except common_exceptions.RedisConnectionError as exc:
            logger.error("RedisConnectionError: {}", Pii(str(exc)))
            # Thrown when cache.ping() fails on cache connection retrieval
            raise HTTPException(
                status_code=HTTP_424_FAILED_DEPENDENCY,
                detail=exc.args[0],
            )
        except Exception as exc:
            logger.error("Exception: {}", Pii(str(exc)))
            failure = {
                "message": "This record could not be added",
                "data": kwargs,
            }
            failed.append(failure)
        else:
            created.append(privacy_request)

    return BulkPostPrivacyRequests(
        succeeded=created,
        failed=failed,
    )


def _process_privacy_request_restart(
    privacy_request: PrivacyRequest,
    failed_step: CurrentStep,
    failed_collection: Optional[CollectionAddress],
    db: Session,
) -> PrivacyRequestResponse:

    logger.info(
        "Restarting failed privacy request '{}' from '{} step, 'collection '{}'",
        privacy_request.id,
        failed_step,
        failed_collection,
    )

    privacy_request.status = PrivacyRequestStatus.in_processing
    privacy_request.save(db=db)
    queue_privacy_request(
        privacy_request_id=privacy_request.id,
        from_step=failed_step.value,
    )

    return privacy_request
