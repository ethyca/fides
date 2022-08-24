# pylint: disable=too-many-branches,too-many-locals,too-many-lines

import csv
import io
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Set, Union

import sqlalchemy
from fastapi import Body, Depends, HTTPException, Security
from fastapi.params import Query as FastAPIQuery
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslib.models.audit_log import AuditLog, AuditLogAction
from fideslib.models.client import ClientDetail
from pydantic import conlist
from sqlalchemy import cast, column, null
from sqlalchemy.orm import Query, Session
from starlette.responses import StreamingResponse
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_424_FAILED_DEPENDENCY,
)

from fidesops.ops import common_exceptions
from fidesops.ops.api import deps
from fidesops.ops.api.v1 import scope_registry as scopes
from fidesops.ops.api.v1 import urn_registry as urls
from fidesops.ops.api.v1.scope_registry import (
    PRIVACY_REQUEST_CALLBACK_RESUME,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_REVIEW,
)
from fidesops.ops.api.v1.urn_registry import (
    PRIVACY_REQUEST_APPROVE,
    PRIVACY_REQUEST_DENY,
    PRIVACY_REQUEST_MANUAL_ERASURE,
    PRIVACY_REQUEST_MANUAL_INPUT,
    PRIVACY_REQUEST_RESUME,
    PRIVACY_REQUEST_RETRY,
    PRIVACY_REQUEST_VERIFY_IDENTITY,
    REQUEST_PREVIEW,
)
from fidesops.ops.common_exceptions import (
    EmailDispatchException,
    FunctionalityNotConfigured,
    IdentityVerificationException,
    TraversalError,
    ValidationError,
)
from fidesops.ops.core.config import config
from fidesops.ops.graph.config import CollectionAddress
from fidesops.ops.graph.graph import DatasetGraph, Node
from fidesops.ops.graph.traversal import Traversal
from fidesops.ops.models.connectionconfig import ConnectionConfig
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.models.policy import PausedStep, Policy, PolicyPreWebhook
from fidesops.ops.models.privacy_request import (
    ExecutionLog,
    PrivacyRequest,
    PrivacyRequestStatus,
    ProvidedIdentity,
)
from fidesops.ops.schemas.dataset import (
    CollectionAddressResponse,
    DryRunDatasetResponse,
)
from fidesops.ops.schemas.email.email import (
    EmailActionType,
    SubjectIdentityVerificationBodyParams,
)
from fidesops.ops.schemas.external_https import PrivacyRequestResumeFormat
from fidesops.ops.schemas.privacy_request import (
    BulkPostPrivacyRequests,
    BulkReviewResponse,
    DenyPrivacyRequests,
    ExecutionLogDetailResponse,
    PrivacyRequestCreate,
    PrivacyRequestResponse,
    PrivacyRequestVerboseResponse,
    ReviewPrivacyRequestIds,
    RowCountRequest,
    StoppedCollection,
    VerificationCode,
)
from fidesops.ops.service.email.email_dispatch_service import dispatch_email
from fidesops.ops.service.privacy_request.request_runner_service import (
    generate_id_verification_code,
    queue_privacy_request,
)
from fidesops.ops.service.privacy_request.request_service import (
    build_required_privacy_request_kwargs,
    cache_data,
)
from fidesops.ops.task.graph_task import EMPTY_REQUEST, collect_queries
from fidesops.ops.task.task_resources import TaskResources
from fidesops.ops.util.api_router import APIRouter
from fidesops.ops.util.cache import FidesopsRedis
from fidesops.ops.util.collection_util import Row
from fidesops.ops.util.logger import Pii
from fidesops.ops.util.oauth_util import verify_callback_oauth, verify_oauth_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Privacy Requests"], prefix=urls.V1_URL_PREFIX)
EMBEDDED_EXECUTION_LOG_LIMIT = 50


def get_privacy_request_or_error(
    db: Session, privacy_request_id: str
) -> PrivacyRequest:
    """Load the privacy request or throw a 404"""
    logger.info("Finding privacy request with id '%s'", privacy_request_id)

    privacy_request = PrivacyRequest.get(db, object_id=privacy_request_id)

    if not privacy_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No privacy request found with id '{privacy_request_id}'.",
        )

    return privacy_request


@router.post(
    urls.PRIVACY_REQUESTS,
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
    if not config.redis.enabled:
        raise FunctionalityNotConfigured(
            "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a redis cache."
        )

    created = []
    failed = []
    # Optional fields to validate here are those that are both nullable in the DB, and exist
    # on the Pydantic schema

    logger.info("Starting creation for %s privacy requests", len(data))

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

        logger.info("Finding policy with key '%s'", privacy_request_data.policy_key)
        policy: Optional[Policy] = Policy.get_by(
            db=db,
            field="key",
            value=privacy_request_data.policy_key,
        )
        if policy is None:
            logger.warning(
                "Create failed for privacy request with invalid policy key %s'",
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

            if config.execution.subject_identity_verification_required:
                _send_verification_code_to_user(
                    db, privacy_request, privacy_request_data.identity.email
                )
                created.append(privacy_request)
                continue  # Skip further processing for this privacy request

            if not config.execution.require_manual_request_approval:
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
        except EmailDispatchException as exc:
            kwargs["privacy_request_id"] = privacy_request.id
            logger.error("EmailDispatchException: %s", exc)
            failure = {
                "message": "Verification email could not be sent.",
                "data": kwargs,
            }
            failed.append(failure)
        except common_exceptions.RedisConnectionError as exc:
            logger.error("RedisConnectionError: %s", Pii(str(exc)))
            # Thrown when cache.ping() fails on cache connection retrieval
            raise HTTPException(
                status_code=HTTP_424_FAILED_DEPENDENCY,
                detail=exc.args[0],
            )
        except Exception as exc:
            logger.error("Exception: %s", Pii(str(exc)))
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


def _send_verification_code_to_user(
    db: Session, privacy_request: PrivacyRequest, email: Optional[str]
) -> None:
    """Generate and cache a verification code, and then email to the user"""
    verification_code: str = generate_id_verification_code()
    privacy_request.cache_identity_verification_code(verification_code)
    dispatch_email(
        db=db,
        action_type=EmailActionType.SUBJECT_IDENTITY_VERIFICATION,
        to_email=email,
        email_body_params=SubjectIdentityVerificationBodyParams(
            verification_code=verification_code,
            verification_code_ttl_seconds=config.redis.identity_verification_code_ttl_seconds,
        ),
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
) -> DefaultDict[str, List["ExecutionLog"]]:
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
                conditions=(ProvidedIdentity.hashed_value == hashed_identity),
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

    return query.order_by(PrivacyRequest.created_at.desc())


def attach_resume_instructions(privacy_request: PrivacyRequest) -> None:
    """
    Temporarily update a paused or errored privacy request object with instructions from the Redis cache
    about how to resume manually if applicable.
    """
    resume_endpoint: Optional[str] = None
    stopped_collection_details: Optional[StoppedCollection] = None

    if privacy_request.status == PrivacyRequestStatus.paused:
        stopped_collection_details = privacy_request.get_paused_collection_details()

        if stopped_collection_details:
            # Graph is paused on a specific collection
            resume_endpoint = (
                PRIVACY_REQUEST_MANUAL_ERASURE
                if stopped_collection_details.step == PausedStep.erasure
                else PRIVACY_REQUEST_MANUAL_INPUT
            )
        else:
            # Graph is paused on a pre-processing webhook
            resume_endpoint = PRIVACY_REQUEST_RESUME

    elif privacy_request.status == PrivacyRequestStatus.error:
        stopped_collection_details = privacy_request.get_failed_collection_details()
        resume_endpoint = PRIVACY_REQUEST_RETRY

    if stopped_collection_details:
        stopped_collection_details.step = stopped_collection_details.step.value  # type: ignore
        stopped_collection_details.collection = (
            stopped_collection_details.collection.value  # type: ignore
        )

    privacy_request.stopped_collection_details = stopped_collection_details
    # replaces the placeholder in the url with the privacy request id
    privacy_request.resume_endpoint = (
        resume_endpoint.format(privacy_request_id=privacy_request.id)
        if resume_endpoint
        else None
    )


@router.get(
    urls.PRIVACY_REQUESTS,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.PRIVACY_REQUEST_READ])],
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
) -> Union[StreamingResponse, AbstractPage[PrivacyRequest]]:
    """Returns PrivacyRequest information. Supports a variety of optional query params.

    To fetch a single privacy request, use the request_id query param `?request_id=`.
    To see individual execution logs, use the verbose query param `?verbose=True`.
    """

    logger.info("Finding all request statuses with pagination params %s", params)
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
    urls.REQUEST_STATUS_LOGS,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.PRIVACY_REQUEST_READ])],
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
        "Finding all execution logs for privacy request %s with params '%s'",
        privacy_request_id,
        params,
    )

    return paginate(
        ExecutionLog.query(db=db)
        .filter(ExecutionLog.privacy_request_id == privacy_request_id)
        .order_by(ExecutionLog.updated_at.asc()),
        params,
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
        logger.info("Dry run failed: %s", err)
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
    cache: FidesopsRedis = Depends(deps.get_cache),
    webhook: PolicyPreWebhook = Security(
        verify_callback_oauth, scopes=[scopes.PRIVACY_REQUEST_CALLBACK_RESUME]
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
        "Resuming privacy request '%s' from webhook '%s'",
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
    expected_paused_step: PausedStep,
    manual_rows: List[Row] = [],
    manual_count: Optional[int] = None,
) -> PrivacyRequest:
    """Resume privacy request after validating and caching manual data for an access or an erasure request."""
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
        StoppedCollection
    ] = privacy_request.get_paused_collection_details()
    if not paused_details:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume privacy request '{privacy_request.id}'; no paused details.",
        )

    paused_step: PausedStep = paused_details.step
    paused_collection: CollectionAddress = paused_details.collection

    if paused_step != expected_paused_step:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Collection '{paused_collection}' is paused at the {paused_step.value} step. Pass in manual data instead to "
            f"'{PRIVACY_REQUEST_MANUAL_ERASURE if paused_step == PausedStep.erasure else PRIVACY_REQUEST_MANUAL_INPUT}' to resume.",
        )

    datasets = DatasetConfig.all(db=db)
    dataset_graphs = [dataset_config.get_graph() for dataset_config in datasets]
    dataset_graph = DatasetGraph(*dataset_graphs)

    node: Optional[Node] = dataset_graph.nodes.get(paused_collection)
    if not node:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot save manual data. No collection in graph with name: '{paused_collection.value}'.",
        )

    if paused_step == PausedStep.access:
        validate_manual_input(manual_rows, paused_collection, dataset_graph)
        logger.info(
            "Caching manual input for privacy request '%s', collection: '%s'",
            privacy_request_id,
            paused_collection,
        )
        privacy_request.cache_manual_input(paused_collection, manual_rows)

    elif paused_step == PausedStep.erasure:
        logger.info(
            "Caching manually erased row count for privacy request '%s', collection: '%s'",
            privacy_request_id,
            paused_collection,
        )
        privacy_request.cache_manual_erasure_count(paused_collection, manual_count)  # type: ignore

    logger.info(
        "Resuming privacy request '%s', %s step, from collection '%s'",
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
    cache: FidesopsRedis = Depends(deps.get_cache),
    manual_rows: List[Row],
) -> PrivacyRequestResponse:
    """Resume a privacy request by passing in manual input for the paused collection.

    If there's no manual data to submit, pass in an empty list to resume the privacy request.
    """
    return resume_privacy_request_with_manual_input(
        privacy_request_id=privacy_request_id,
        db=db,
        expected_paused_step=PausedStep.access,
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
        expected_paused_step=PausedStep.erasure,
        manual_count=manual_count.row_count,
    )


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
        StoppedCollection
    ] = privacy_request.get_failed_collection_details()
    if not failed_details:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot restart privacy request from failure '{privacy_request.id}'; no failed step or collection.",
        )

    failed_step: PausedStep = failed_details.step
    failed_collection: CollectionAddress = failed_details.collection

    logger.info(
        "Restarting failed privacy request '%s' from '%s step, 'collection '%s'",
        privacy_request_id,
        failed_step,
        failed_collection,
    )

    privacy_request.status = PrivacyRequestStatus.in_processing
    privacy_request.save(db=db)
    queue_privacy_request(
        privacy_request_id=privacy_request.id,
        from_step=failed_step.value,
    )

    privacy_request.cache_failed_collection_details()  # Reset failed step and collection to None

    return privacy_request


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
    except IdentityVerificationException as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=exc.message)
    except PermissionError as exc:
        logger.info("Invalid verification code provided for %s.", privacy_request.id)
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=exc.args[0])

    logger.info("Identity verified for %s.", privacy_request.id)

    if not config.execution.require_manual_request_approval:
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

        AuditLog.create(
            db=db,
            data={
                "user_id": user_id,
                "privacy_request_id": privacy_request.id,
                "action": AuditLogAction.denied,
                "message": privacy_requests.reason,
            },
        )
        privacy_request.status = PrivacyRequestStatus.denied
        privacy_request.reviewed_at = datetime.utcnow()
        privacy_request.reviewed_by = user_id
        privacy_request.save(db=db)

    return review_privacy_request(
        db=db,
        request_ids=privacy_requests.request_ids,
        process_request_function=_deny_request,
    )
