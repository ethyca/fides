# pylint: disable=too-many-branches,too-many-lines, too-many-statements

import csv
import io
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, DefaultDict, Dict, List, Literal, Optional, Set, Union

import sqlalchemy
from fastapi import Body, Depends, HTTPException, Security
from fastapi.params import Query as FastAPIQuery
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from pydantic import ValidationError as PydanticValidationError
from pydantic import conlist
from sqlalchemy import cast, column, null, or_, select
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

from fides.api import common_exceptions
from fides.api.api import deps
from fides.api.api.v1.endpoints.dataset_endpoints import _get_connection_config
from fides.api.api.v1.endpoints.manual_webhook_endpoints import (
    get_access_manual_webhook_or_404,
)
from fides.api.common_exceptions import (
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
from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.graph.traversal import Traversal
from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.manual_webhook import AccessManualWebhook
from fides.api.models.policy import CurrentStep, Policy, PolicyPreWebhook, Rule
from fides.api.models.pre_approval_webhook import (
    PreApprovalWebhook,
    PreApprovalWebhookReply,
)
from fides.api.models.privacy_preference import PrivacyPreferenceHistory
from fides.api.models.privacy_request import (
    CheckpointActionRequired,
    ConsentRequest,
    CustomPrivacyRequestField,
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequest,
    PrivacyRequestNotifications,
    PrivacyRequestStatus,
    ProvidedIdentity,
    ProvidedIdentityType,
    RequestTask,
)
from fides.api.models.property import Property
from fides.api.oauth.utils import (
    verify_callback_oauth_policy_pre_webhook,
    verify_callback_oauth_pre_approval_webhook,
    verify_oauth_client,
    verify_request_task_callback,
)
from fides.api.schemas.dataset import CollectionAddressResponse, DryRunDatasetResponse
from fides.api.schemas.external_https import PrivacyRequestResumeFormat
from fides.api.schemas.messaging.messaging import (
    FidesopsMessage,
    MessagingActionType,
    RequestReceiptBodyParams,
    RequestReviewDenyBodyParams,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import (
    BulkPostPrivacyRequests,
    BulkReviewResponse,
    DenyPrivacyRequests,
    ExecutionLogDetailResponse,
    ManualWebhookData,
    PrivacyRequestCreate,
    PrivacyRequestFilter,
    PrivacyRequestNotificationInfo,
    PrivacyRequestResponse,
    PrivacyRequestTaskSchema,
    PrivacyRequestVerboseResponse,
    RequestTaskCallbackRequest,
    ReviewPrivacyRequestIds,
    VerificationCode,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.service._verification import send_verification_code_to_user
from fides.api.service.messaging.message_dispatch_service import (
    EMAIL_JOIN_STRING,
    check_and_dispatch_error_notifications,
    dispatch_message_task,
    message_send_enabled,
)
from fides.api.service.privacy_request.request_runner_service import (
    queue_privacy_request,
)
from fides.api.service.privacy_request.request_service import (
    build_required_privacy_request_kwargs,
    cache_data,
)
from fides.api.task.execute_request_tasks import log_task_queued, queue_request_task
from fides.api.task.filter_results import filter_data_categories
from fides.api.task.graph_task import EMPTY_REQUEST, EMPTY_REQUEST_TASK, collect_queries
from fides.api.task.task_resources import TaskResources
from fides.api.tasks import MESSAGING_QUEUE_NAME
from fides.api.util.api_router import APIRouter
from fides.api.util.cache import FidesopsRedis
from fides.api.util.collection_util import Row
from fides.api.util.endpoint_utils import validate_start_and_end_filters
from fides.api.util.enums import ColumnSort
from fides.api.util.logger import Pii
from fides.common.api.scope_registry import (
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
from fides.common.api.v1.urn_registry import (
    PRIVACY_REQUEST_APPROVE,
    PRIVACY_REQUEST_AUTHENTICATED,
    PRIVACY_REQUEST_BULK_RETRY,
    PRIVACY_REQUEST_DENY,
    PRIVACY_REQUEST_MANUAL_WEBHOOK_ACCESS_INPUT,
    PRIVACY_REQUEST_MANUAL_WEBHOOK_ERASURE_INPUT,
    PRIVACY_REQUEST_NOTIFICATIONS,
    PRIVACY_REQUEST_PRE_APPROVE_ELIGIBLE,
    PRIVACY_REQUEST_PRE_APPROVE_NOT_ELIGIBLE,
    PRIVACY_REQUEST_REQUEUE,
    PRIVACY_REQUEST_RESUME,
    PRIVACY_REQUEST_RESUME_FROM_REQUIRES_INPUT,
    PRIVACY_REQUEST_RETRY,
    PRIVACY_REQUEST_SEARCH,
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

router = APIRouter(tags=["Privacy Requests"], prefix=V1_URL_PREFIX)

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
    config_proxy: ConfigProxy = Depends(deps.get_config_proxy),
    data: conlist(PrivacyRequestCreate, max_items=50) = Body(...),  # type: ignore
) -> BulkPostPrivacyRequests:
    """
    Given a list of privacy request data elements, create corresponding PrivacyRequest objects
    or report failure and execute them within the Fidesops system.
    You cannot update privacy requests after they've been created.
    """
    return create_privacy_request_func(db, config_proxy, data, False)


@router.post(
    PRIVACY_REQUEST_AUTHENTICATED,
    status_code=HTTP_200_OK,
    dependencies=[Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_CREATE])],
    response_model=BulkPostPrivacyRequests,
)
def create_privacy_request_authenticated(
    *,
    db: Session = Depends(deps.get_db),
    config_proxy: ConfigProxy = Depends(deps.get_config_proxy),
    data: conlist(PrivacyRequestCreate, max_items=50) = Body(...),  # type: ignore
) -> BulkPostPrivacyRequests:
    """
    Given a list of privacy request data elements, create corresponding PrivacyRequest objects
    or report failure and execute them within the Fidesops system.
    You cannot update privacy requests after they've been created.
    This route requires authentication instead of using verification codes.
    """
    return create_privacy_request_func(db, config_proxy, data, True)


def _send_privacy_request_receipt_message_to_user(
    policy: Optional[Policy],
    to_identity: Optional[Identity],
    service_type: Optional[str],
    property_id: Optional[str],
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
            "service_type": service_type,
            "to_identity": to_identity.dict(),
            "property_id": property_id,
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
            "Status",
            "Request Type",
            "Subject Identity",
            "Custom Privacy Request Fields",
            "Time Received",
            "Reviewed By",
            "Request ID",
            "Time Approved/Denied",
            "Denial Reason",
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
                pr.status.value if pr.status else None,
                pr.policy.rules[0].action_type if len(pr.policy.rules) > 0 else None,
                pr.get_persisted_identity().dict(),
                pr.get_persisted_custom_privacy_request_fields(),
                pr.created_at,
                pr.reviewed_by,
                pr.id,
                pr.reviewed_at,
                denial_reason,
            ]
        )

    f.seek(0)
    response = StreamingResponse(f, media_type="text/csv")
    response.headers["Content-Disposition"] = (
        f"attachment; filename=privacy_requests_download_{datetime.today().strftime('%Y-%m-%d')}.csv"
    )
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
        cast(AuditLog.action.label("status"), sqlalchemy.String).label("status"),
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


def _filter_privacy_request_queryset(
    db: Session,
    query: Query,
    request_id: Optional[str] = None,
    identity: Optional[str] = None,
    identities: Optional[Dict[str, Any]] = None,
    custom_privacy_request_fields: Optional[Dict[str, Any]] = None,
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
    action_type: Optional[ActionType] = None,
) -> Query:
    """
    Utility method to apply filters to our privacy request query.

    Status supports "or" filtering:
    `status=["approved","pending"]` will be translated into an "or" query.

    The `identities` and `custom_privacy_request_fields` parameters allow
    searching for privacy requests that match any of the provided identities
    or custom privacy request fields, respectively. The filtering is performed
    using an "or" condition, meaning that a privacy request will be included
    in the results if it matches at least one of the provided identities or
    custom privacy request fields.
    """

    if any([completed_lt, completed_gt]) and any([errored_lt, errored_gt]):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Cannot specify both succeeded and failed query params.",
        )

    validate_start_and_end_filters(
        [
            (created_lt, created_gt, "created"),
            (completed_lt, completed_gt, "completed"),
            (errored_lt, errored_gt, "errored"),
            (started_lt, started_gt, "started"),
        ]
    )

    if identity:
        hashed_identity = ProvidedIdentity.hash_value(value=identity)
        identity_set: Set[str] = {
            identity[0]
            for identity in ProvidedIdentity.filter(
                db=db,
                conditions=(
                    (ProvidedIdentity.hashed_value == hashed_identity)
                    & (ProvidedIdentity.privacy_request_id.isnot(None))
                ),
            ).values(column("privacy_request_id"))
        }
        query = query.filter(PrivacyRequest.id.in_(identity_set))

    if identities:
        identity_conditions = [
            (ProvidedIdentity.field_name == field_name)
            & (ProvidedIdentity.hashed_value == ProvidedIdentity.hash_value(value))
            for field_name, value in identities.items()
        ]

        identities_query = select([ProvidedIdentity.privacy_request_id]).where(
            or_(*identity_conditions)
            & (ProvidedIdentity.privacy_request_id.isnot(None))
        )
        query = query.filter(PrivacyRequest.id.in_(identities_query))

    if custom_privacy_request_fields:
        # Note that if Custom Privacy Request Field values were arrays, they are not
        # indexed for searching and not discoverable here
        custom_field_conditions = [
            (CustomPrivacyRequestField.field_name == field_name)
            & (
                CustomPrivacyRequestField.hashed_value
                == CustomPrivacyRequestField.hash_value(value)
            )
            for field_name, value in custom_privacy_request_fields.items()
            if not isinstance(value, list)
        ]

        custom_fields_query = select(
            [CustomPrivacyRequestField.privacy_request_id]
        ).where(
            or_(*custom_field_conditions)
            & (CustomPrivacyRequestField.privacy_request_id.isnot(None))
        )
        query = query.filter(PrivacyRequest.id.in_(custom_fields_query))

    # Further restrict all PrivacyRequests by additional params
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
    if action_type:
        policy_ids_for_action_type = (
            db.query(Rule)
            .filter(Rule.action_type == action_type)
            .with_entities(Rule.policy_id)
            .distinct()
        )
        query = query.filter(PrivacyRequest.policy_id.in_(policy_ids_for_action_type))

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


def _shared_privacy_request_search(
    *,
    db: Session,
    params: Params,
    request_id: Optional[str] = None,
    identity: Optional[str] = None,
    identities: Optional[Dict[str, str]] = None,
    custom_privacy_request_fields: Optional[Dict[str, Any]] = None,
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
    action_type: Optional[ActionType] = None,
    verbose: Optional[bool] = False,
    include_identities: Optional[bool] = False,
    include_custom_privacy_request_fields: Optional[bool] = False,
    download_csv: Optional[bool] = False,
    sort_field: str = "created_at",
    sort_direction: ColumnSort = ColumnSort.DESC,
) -> Union[StreamingResponse, AbstractPage[PrivacyRequest]]:
    """
    Internal function to handle the logic for retrieving privacy requests.

    This function is used by both the GET and POST versions of the privacy request endpoints
    to avoid duplicating the logic while transitioning from the GET version to the
    POST version of the endpoint.
    """

    logger.info("Finding all request statuses with pagination params {}", params)

    query = db.query(PrivacyRequest)
    query = _filter_privacy_request_queryset(
        db,
        query,
        request_id,
        identity,
        identities,
        custom_privacy_request_fields,
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
        action_type,
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

    for item in paginated.items:  # type: ignore
        if include_identities:
            item.identity = item.get_persisted_identity().labeled_dict(
                include_default_labels=True
            )

        if include_custom_privacy_request_fields:
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
    action_type: Optional[ActionType] = None,
    verbose: Optional[bool] = False,
    include_identities: Optional[bool] = False,
    include_custom_privacy_request_fields: Optional[bool] = False,
    download_csv: Optional[bool] = False,
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

    # Both the old and new versions of the privacy request search endpoints use this shared function.
    # The `identities` and `custom_privacy_request_fields` parameters are only supported in the new version
    # so they are both set to None here.
    return _shared_privacy_request_search(
        db=db,
        params=params,
        request_id=request_id,
        identity=identity,
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
        action_type=action_type,
        verbose=verbose,
        include_identities=include_identities,
        include_custom_privacy_request_fields=include_custom_privacy_request_fields,
        download_csv=download_csv,
        sort_field=sort_field,
        sort_direction=sort_direction,
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

    return _shared_privacy_request_search(
        db=db,
        params=params,
        request_id=privacy_request_filter.request_id,
        identities=privacy_request_filter.identities,
        custom_privacy_request_fields=privacy_request_filter.custom_privacy_request_fields,
        status=privacy_request_filter.status,  # type: ignore
        created_lt=privacy_request_filter.created_lt,
        created_gt=privacy_request_filter.created_gt,
        started_lt=privacy_request_filter.started_lt,
        started_gt=privacy_request_filter.started_gt,
        completed_lt=privacy_request_filter.completed_lt,
        completed_gt=privacy_request_filter.completed_gt,
        errored_lt=privacy_request_filter.errored_lt,
        errored_gt=privacy_request_filter.errored_gt,
        external_id=privacy_request_filter.external_id,
        action_type=privacy_request_filter.action_type,
        verbose=privacy_request_filter.verbose,
        include_identities=privacy_request_filter.include_identities,
        include_custom_privacy_request_fields=privacy_request_filter.include_custom_privacy_request_fields,
        download_csv=privacy_request_filter.download_csv,
        sort_field=privacy_request_filter.sort_field,
        sort_direction=privacy_request_filter.sort_direction,
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
    privacy_request_ids: List[str],
    *,
    db: Session = Depends(deps.get_db),
) -> BulkPostPrivacyRequests:
    """Bulk restart a of privacy request from failure."""
    succeeded: List[PrivacyRequestResponse] = []
    failed: List[Dict[str, Any]] = []
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
) -> PrivacyRequestResponse:
    """Restart a privacy request from failure"""
    privacy_request: PrivacyRequest = get_privacy_request_or_error(
        db, privacy_request_id
    )

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


def review_privacy_request(
    db: Session,
    request_ids: List[str],
    process_request_function: Callable,
    config_proxy: ConfigProxy,
    webhook_id: Optional[str],
    user_id: Optional[str],
) -> BulkReviewResponse:
    """Helper method shared between the approve and deny privacy request endpoints, and pre-approval webhook endpoints"""
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
            process_request_function(
                db, config_proxy, privacy_request, webhook_id, user_id
            )
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
    service_type: Optional[str],
    property_id: Optional[str],
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
                body_params=(
                    RequestReviewDenyBodyParams(rejection_reason=rejection_reason)
                    if action_type is MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY
                    else None
                ),
            ).dict(),
            "service_type": service_type,
            "to_identity": to_identity.dict(),
            "property_id": property_id,
        },
    )


def _trigger_pre_approval_webhooks(
    db: Session, privacy_request: PrivacyRequest
) -> None:
    """
    Shared method to trigger all configured pre-approval webhooks for a given privacy request.
    """
    pre_approval_webhooks = db.query(PreApprovalWebhook).all()
    for webhook in pre_approval_webhooks:
        privacy_request.trigger_pre_approval_webhook(
            webhook=webhook,
            policy_action=privacy_request.policy.get_action_type(),
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
        if message_send_enabled(
            db,
            privacy_request.property_id,
            MessagingActionType.PRIVACY_REQUEST_RECEIPT,
            config_proxy.notifications.send_request_receipt_notification,
        ):
            _send_privacy_request_receipt_message_to_user(
                policy,
                privacy_request.get_persisted_identity(),
                config_proxy.notifications.notification_service_type,
                privacy_request.property_id,
            )

    except IdentityVerificationException as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=exc.message)
    except PermissionError as exc:
        logger.info("Invalid verification code provided for {}.", privacy_request.id)
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=exc.args[0])

    logger.info("Identity verified for {}.", privacy_request.id)

    if config_proxy.execution.require_manual_request_approval:
        _trigger_pre_approval_webhooks(db, privacy_request)
    else:
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

    return privacy_request  # type: ignore[return-value]


def _approve_request(
    db: Session,
    config_proxy: ConfigProxy,
    privacy_request: PrivacyRequest,
    webhook_id: Optional[str],
    user_id: Optional[str],
) -> None:
    """Method for how to process requests - approved"""
    now = datetime.utcnow()
    privacy_request.status = PrivacyRequestStatus.approved
    privacy_request.reviewed_at = now
    if user_id:
        privacy_request.reviewed_by = user_id

    if privacy_request.custom_fields:  # type: ignore[attr-defined]
        privacy_request.custom_privacy_request_fields_approved_at = now
        if user_id:
            # for now, the reviewer will be marked as the approver of the custom privacy request fields
            # this is to make it flexible in the future if we want to allow a different user to approve
            privacy_request.custom_privacy_request_fields_approved_by = user_id
    privacy_request.save(db=db)

    auditlog_data = {
        "privacy_request_id": privacy_request.id,
        "action": AuditLogAction.approved,
        "message": "",
        "user_id": user_id if user_id else None,
        "webhook_id": (
            webhook_id if webhook_id else None
        ),  # the last webhook reply received is what approves the entire request
    }
    AuditLog.create(
        db=db,
        data=auditlog_data,
    )
    if message_send_enabled(
        db,
        privacy_request.property_id,
        MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE,
        config_proxy.notifications.send_request_review_notification,
    ):
        _send_privacy_request_review_message_to_user(
            action_type=MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE,
            identity_data=privacy_request.get_cached_identity_data(),
            rejection_reason=None,
            service_type=config_proxy.notifications.notification_service_type,
            property_id=privacy_request.property_id,
        )

    queue_privacy_request(privacy_request_id=privacy_request.id)


@router.patch(
    PRIVACY_REQUEST_APPROVE,
    status_code=HTTP_200_OK,
    response_model=BulkReviewResponse,
)
def approve_privacy_request(
    *,
    db: Session = Depends(deps.get_db),
    config_proxy: ConfigProxy = Depends(deps.get_config_proxy),
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[PRIVACY_REQUEST_REVIEW],
    ),
    privacy_requests: ReviewPrivacyRequestIds,
) -> BulkReviewResponse:
    """Approve and dispatch a list of privacy requests and/or report failure"""
    user_id = client.user_id

    return review_privacy_request(
        db=db,
        request_ids=privacy_requests.request_ids,
        config_proxy=config_proxy,
        process_request_function=_approve_request,
        user_id=user_id,
        webhook_id=None,
    )


@router.patch(
    PRIVACY_REQUEST_DENY,
    status_code=HTTP_200_OK,
    response_model=BulkReviewResponse,
)
def deny_privacy_request(
    *,
    db: Session = Depends(deps.get_db),
    config_proxy: ConfigProxy = Depends(deps.get_config_proxy),
    client: ClientDetail = Security(
        verify_oauth_client,
        scopes=[PRIVACY_REQUEST_REVIEW],
    ),
    privacy_requests: DenyPrivacyRequests,
) -> BulkReviewResponse:
    """Deny a list of privacy requests and/or report failure"""
    user_id = client.user_id

    def _deny_request(
        db: Session,
        config_proxy: ConfigProxy,
        privacy_request: PrivacyRequest,
        webhook_id: Optional[str],
        user_id: Optional[str],
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

        if message_send_enabled(
            db,
            privacy_request.property_id,
            MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY,
            config_proxy.notifications.send_request_review_notification,
        ):
            _send_privacy_request_review_message_to_user(
                action_type=MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY,
                identity_data=privacy_request.get_cached_identity_data(),
                rejection_reason=privacy_requests.reason,
                service_type=config_proxy.notifications.notification_service_type,
                property_id=privacy_request.property_id,
            )

    return review_privacy_request(
        db=db,
        config_proxy=config_proxy,
        request_ids=privacy_requests.request_ids,
        process_request_function=_deny_request,
        user_id=user_id,
        webhook_id=None,
    )


def _validate_privacy_request_pending_or_error(
    db: Session, privacy_request_id: str
) -> None:
    privacy_request = PrivacyRequest.get(db, object_id=privacy_request_id)
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
    config_proxy: ConfigProxy = Depends(deps.get_config_proxy),
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
    review_privacy_request(
        db=db,
        request_ids=[privacy_request_id],
        config_proxy=config_proxy,
        process_request_function=_approve_request,
        webhook_id=webhook.id,
        user_id=None,
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
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()
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
        db, privacy_request_id
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
        db, privacy_request_id
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


def create_privacy_request_func(
    db: Session,
    config_proxy: ConfigProxy,
    data: conlist(PrivacyRequestCreate),  # type: ignore
    authenticated: bool = False,
    privacy_preferences: List[
        PrivacyPreferenceHistory
    ] = [],  # For consent requests only
) -> BulkPostPrivacyRequests:
    """Creates privacy requests.

    If authenticated is True the identity verification step is bypassed.
    """
    # TODO: (PROD-2142)- update privacy center to pass in property id where applicable
    if not CONFIG.redis.enabled:
        raise FunctionalityNotConfigured(
            "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a redis cache."
        )

    created = []
    failed = []
    # Optional fields to validate here are those that are both nullable in the DB, and exist
    # on the Pydantic schema

    logger.info("Starting creation for {} privacy requests", len(data))

    optional_fields = [
        "external_id",
        "started_processing_at",
        "finished_processing_at",
        "consent_preferences",
        "property_id",
    ]
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

        if privacy_request_data.property_id:
            valid_property: Optional[Property] = Property.get_by(
                db, field="id", value=privacy_request_data.property_id
            )
            if not valid_property:
                logger.warning(
                    "Create failed for privacy request with invalid property id"
                )
                failure = {
                    "message": "Property id must be valid to process",
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
            privacy_request_data.requested_at,
            policy.id,
            config_proxy.execution.subject_identity_verification_required,
            authenticated,
        )
        for field in optional_fields:
            attr = getattr(privacy_request_data, field)
            if attr is not None:
                if field == "consent_preferences":
                    attr = [consent.dict() for consent in attr]

                kwargs[field] = attr

        try:
            privacy_request: PrivacyRequest = PrivacyRequest.create(db=db, data=kwargs)
            privacy_request.persist_identity(
                db=db, identity=privacy_request_data.identity
            )
            _create_or_update_custom_fields(
                db,
                privacy_request,
                privacy_request_data.consent_request_id,
                privacy_request_data.custom_privacy_request_fields,
            )
            for privacy_preference in privacy_preferences:
                privacy_preference.privacy_request_id = privacy_request.id
                privacy_preference.save(db=db)

            cache_data(
                privacy_request,
                policy,
                privacy_request_data.identity,
                privacy_request_data.encryption_key,
                None,
                privacy_request_data.custom_privacy_request_fields,
            )

            check_and_dispatch_error_notifications(db=db)

            if not authenticated and message_send_enabled(
                db,
                privacy_request.property_id,
                MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
                config_proxy.execution.subject_identity_verification_required,
            ):
                send_verification_code_to_user(
                    db,
                    privacy_request,
                    privacy_request_data.identity,
                    privacy_request.property_id,
                )
                created.append(privacy_request)
                continue  # Skip further processing for this privacy request

            if not authenticated and message_send_enabled(
                db,
                privacy_request.property_id,
                MessagingActionType.PRIVACY_REQUEST_RECEIPT,
                config_proxy.notifications.send_request_receipt_notification,
            ):
                _send_privacy_request_receipt_message_to_user(
                    policy,
                    privacy_request_data.identity,
                    config_proxy.notifications.notification_service_type,
                    privacy_request.property_id,
                )
            if config_proxy.execution.require_manual_request_approval:
                _trigger_pre_approval_webhooks(db, privacy_request)
            else:
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
            as_string = Pii(str(exc))
            error_cls = str(exc.__class__.__name__)
            logger.error(f"Exception {error_cls}: {as_string}")
            failure = {
                "message": "This record could not be added",
                "data": kwargs,
            }
            failed.append(failure)
        else:
            created.append(privacy_request)

    # TODO: Don't return a 200 if there are failed requests, or at least not
    # if there are zero successful ones
    return BulkPostPrivacyRequests(
        succeeded=created,
        failed=failed,
    )


def _create_or_update_custom_fields(
    db: Session,
    privacy_request: PrivacyRequest,
    consent_request_id: Optional[str],
    custom_privacy_request_fields: Optional[Dict[str, Any]],
) -> None:
    """
    Updates existing custom privacy request fields in the database with a privacy request ID.
    Creates new custom privacy request fields if there aren't any available.

    The presence or absence of custom fields is based on whether or not the creation of this
    current privacy request was triggered by a consent request.
    """
    consent_request = ConsentRequest.get_by_key_or_id(
        db=db, data={"id": consent_request_id}
    )
    if consent_request and consent_request.custom_fields:
        for custom_field in consent_request.custom_fields:  # type: ignore[attr-defined]
            custom_field.privacy_request_id = privacy_request.id
            custom_field.save(db=db)
    elif custom_privacy_request_fields:
        privacy_request.persist_custom_privacy_request_fields(
            db=db,
            custom_privacy_request_fields=custom_privacy_request_fields,
        )


def _process_privacy_request_restart(
    privacy_request: PrivacyRequest,
    failed_step: Optional[CurrentStep],
    db: Session,
) -> PrivacyRequestResponse:
    """If failed_step is provided, restart the DSR within that step. Otherwise,
    restart the privacy request from the beginning."""
    if failed_step:
        logger.info(
            "Restarting failed privacy request '{}' from '{}'",
            privacy_request.id,
            failed_step,
        )
    else:
        logger.info(
            "Restarting failed privacy request '{}' from the beginning",
            privacy_request.id,
        )

    privacy_request.status = PrivacyRequestStatus.in_processing
    privacy_request.save(db=db)
    queue_privacy_request(
        privacy_request_id=privacy_request.id,
        from_step=failed_step.value if failed_step else None,
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
    pr: PrivacyRequest = get_privacy_request_or_error(db, privacy_request_id)

    logger.info(f"Getting Request Tasks for '{privacy_request_id}'")

    return pr.request_tasks.order_by(
        RequestTask.created_at.asc(), RequestTask.collection_address.asc()
    ).all()


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
    pr: PrivacyRequest = get_privacy_request_or_error(db, privacy_request_id)

    if pr.status not in [
        PrivacyRequestStatus.approved,
        PrivacyRequestStatus.in_processing,
    ]:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Request failed. Cannot re-queue privacy request {pr.id} with status {pr.status.value}",
        )

    # Both DSR 2.0 and 3.0 cache checkpoint details
    checkpoint_details: Optional[CheckpointActionRequired] = (
        pr.get_failed_checkpoint_details()
    )
    resume_step = checkpoint_details.step if checkpoint_details else None

    # DSR 3.0 additionally stores Request Tasks in the application db that can be used to infer
    # a resume checkpoint in the event the cache has expired.
    if not resume_step and pr.request_tasks.count():
        if pr.consent_tasks.count():
            resume_step = CurrentStep.consent
        elif pr.erasure_tasks.count():
            # Checking if access terminator task was completed, because erasure tasks are created
            # at the same time as the access tasks
            terminator_access_task = pr.get_terminate_task_by_action(ActionType.access)
            resume_step = (
                CurrentStep.erasure
                if terminator_access_task.status == ExecutionLogStatus.complete
                else CurrentStep.access
            )
        elif pr.access_tasks.count():
            resume_step = CurrentStep.access

    logger.info(
        "Manually re-queuing Privacy Request {} from step {}",
        pr,
        resume_step.value if resume_step else None,
    )

    return _process_privacy_request_restart(
        pr,
        resume_step,
        db,
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
            detail=f"Callback failed. Cannot queue {request_task.action_type.value} task '{request_task.id}' with privacy request status '{privacy_request.status.value}'",
        )
    if request_task.status != ExecutionLogStatus.awaiting_processing:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Callback failed. Cannot queue {request_task.action_type.value} task '{request_task.id}' with request task status '{request_task.status.value}'",
        )
    logger.info(
        "Callback received for {} task {} {}",
        request_task.action_type.value,
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
