import logging
from typing import Any, Dict, List, Optional

import jwt
from fastapi import Depends, HTTPException, Security
from fidesops.ops import common_exceptions
from fidesops.ops.api import deps
from fidesops.ops.api.v1 import scope_registry as scopes
from fidesops.ops.api.v1 import urn_registry as urls
from fidesops.ops.api.v1.endpoints.privacy_request_endpoints import (
    get_privacy_request_or_error,
)
from fidesops.ops.core.config import config
from fidesops.ops.models.policy import DrpAction, Policy
from fidesops.ops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fidesops.ops.schemas.drp_privacy_request import (
    DRP_VERSION,
    DrpDataRightsResponse,
    DrpIdentity,
    DrpPrivacyRequestCreate,
    DrpRevokeRequest,
)
from fidesops.ops.schemas.privacy_request import PrivacyRequestDRPStatusResponse
from fidesops.ops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.ops.service.drp.drp_fidesops_mapper import DrpFidesopsMapper
from fidesops.ops.service.privacy_request.request_runner_service import (
    queue_privacy_request,
)
from fidesops.ops.service.privacy_request.request_service import (
    build_required_privacy_request_kwargs,
    cache_data,
)
from fidesops.ops.util.api_router import APIRouter
from fidesops.ops.util.cache import FidesopsRedis
from fidesops.ops.util.oauth_util import verify_oauth_client
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_424_FAILED_DEPENDENCY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["DRP"], prefix=urls.V1_URL_PREFIX)
EMBEDDED_EXECUTION_LOG_LIMIT = 50


@router.post(
    urls.DRP_EXERCISE,
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestDRPStatusResponse,
)
def create_drp_privacy_request(
    *,
    cache: FidesopsRedis = Depends(deps.get_cache),
    db: Session = Depends(deps.get_db),
    data: DrpPrivacyRequestCreate,
) -> PrivacyRequestDRPStatusResponse:
    """
    Given a drp privacy request body, create and execute
    a corresponding Fidesops PrivacyRequest
    """

    jwt_key: str = config.security.drp_jwt_secret
    if jwt_key is None:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT key must be provided",
        )

    logger.info(f"Finding policy with drp action '{data.exercise[0]}'")
    policy: Optional[Policy] = Policy.get_by(
        db=db,
        field="drp_action",
        value=data.exercise[0],
    )

    if not policy:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No policy found with drp action '{data.exercise}'.",
        )

    privacy_request_kwargs: Dict[str, Any] = build_required_privacy_request_kwargs(
        None, policy.id
    )

    try:
        decrypted_identity: DrpIdentity = DrpIdentity(
            **jwt.decode(data.identity, jwt_key, algorithms=["HS256"])
        )

        mapped_identity: PrivacyRequestIdentity = DrpFidesopsMapper.map_identity(
            drp_identity=decrypted_identity
        )

        privacy_request: PrivacyRequest = PrivacyRequest.create(
            db=db,
            data=privacy_request_kwargs,
        )
        privacy_request.persist_identity(
            db=db,
            identity=mapped_identity,
        )

        logger.info(f"Decrypting identity for DRP privacy request {privacy_request.id}")

        cache_data(privacy_request, policy, mapped_identity, None, data)

        queue_privacy_request(privacy_request.id)

        return PrivacyRequestDRPStatusResponse(
            request_id=privacy_request.id,
            received_at=privacy_request.requested_at,
            status=DrpFidesopsMapper.map_status(privacy_request.status),  # type: ignore
        )

    except common_exceptions.RedisConnectionError as exc:
        logger.error("RedisConnectionError: %s", exc)
        # Thrown when cache.ping() fails on cache connection retrieval
        raise HTTPException(
            status_code=HTTP_424_FAILED_DEPENDENCY,
            detail=exc.args[0],
        )
    except Exception as exc:
        logger.error(f"Exception: {exc}")
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="DRP privacy request could not be exercised",
        )


@router.get(
    urls.DRP_STATUS,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.PRIVACY_REQUEST_READ])],
    response_model=PrivacyRequestDRPStatusResponse,
)
def get_request_status_drp(
    *, db: Session = Depends(deps.get_db), request_id: str
) -> PrivacyRequestDRPStatusResponse:
    """
    Returns PrivacyRequest information where the respective privacy request is associated with
    a policy that implements a Data Rights Protocol action.
    """

    logger.info(f"Finding request for DRP with ID: {request_id}")
    request = PrivacyRequest.get(
        db=db,
        object_id=request_id,
    )
    if not request or not request.policy or not request.policy.drp_action:
        # If no request is found with this ID, or that request has no policy,
        # or that request's policy has no associated drp_action.
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Privacy request with ID {request_id} does not exist, or is not associated with a data rights protocol action.",
        )

    logger.info(f"Privacy request with ID: {request_id} found for DRP status.")
    return PrivacyRequestDRPStatusResponse(
        request_id=request.id,
        received_at=request.requested_at,
        status=DrpFidesopsMapper.map_status(request.status),
    )


@router.get(
    urls.DRP_DATA_RIGHTS,
    dependencies=[Security(verify_oauth_client, scopes=[scopes.POLICY_READ])],
    response_model=DrpDataRightsResponse,
)
def get_drp_data_rights(*, db: Session = Depends(deps.get_db)) -> DrpDataRightsResponse:
    """
    Query all policies and determine the list of DRP actions that are attached to existing policies.
    """

    logger.info("Fetching available DRP data rights")
    actions: List[DrpAction] = [
        item.drp_action  # type: ignore
        for item in db.query(Policy.drp_action).filter(Policy.drp_action.isnot(None))
    ]

    return DrpDataRightsResponse(
        version=DRP_VERSION, api_base=None, actions=actions, user_relationships=None
    )


@router.post(
    urls.DRP_REVOKE,
    dependencies=[
        Security(verify_oauth_client, scopes=[scopes.PRIVACY_REQUEST_REVIEW])
    ],
    response_model=PrivacyRequestDRPStatusResponse,
)
def revoke_request(
    *, db: Session = Depends(deps.get_db), data: DrpRevokeRequest
) -> PrivacyRequestDRPStatusResponse:
    """
    Revoke a pending privacy request.
    """
    privacy_request: PrivacyRequest = get_privacy_request_or_error(db, data.request_id)

    if privacy_request.status != PrivacyRequestStatus.pending:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid revoke request. Can only revoke `pending` requests. Privacy request '{privacy_request.id}' status = {privacy_request.status.value}.",  # type: ignore
        )

    logger.info(f"Canceling privacy request '{privacy_request.id}'")
    privacy_request.cancel_processing(db, cancel_reason=data.reason)

    return PrivacyRequestDRPStatusResponse(
        request_id=privacy_request.id,
        received_at=privacy_request.requested_at,
        status=DrpFidesopsMapper.map_status(privacy_request.status),  # type: ignore
        reason=data.reason,
    )
