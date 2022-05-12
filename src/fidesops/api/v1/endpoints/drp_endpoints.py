import logging
from typing import Dict, Any, Optional

import jwt
from fastapi import HTTPException, Depends, APIRouter, Security
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_424_FAILED_DEPENDENCY,
    HTTP_200_OK,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from fidesops import common_exceptions
from fidesops.api import deps
from fidesops.api.v1 import scope_registry as scopes
from fidesops.api.v1 import urn_registry as urls
from fidesops.core.config import config
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.drp_privacy_request import DrpPrivacyRequestCreate, DrpIdentity
from fidesops.schemas.privacy_request import PrivacyRequestDRPStatusResponse
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.service.drp.drp_fidesops_mapper import DrpFidesopsMapper
from fidesops.service.privacy_request.request_runner_service import PrivacyRequestRunner
from fidesops.service.privacy_request.request_service import (
    build_required_privacy_request_kwargs,
    cache_data,
)
from fidesops.util.cache import FidesopsRedis
from fidesops.util.oauth_util import verify_oauth_client

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

    jwt_key: str = config.security.DRP_JWT_SECRET
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
        privacy_request: PrivacyRequest = PrivacyRequest.create(
            db=db, data=privacy_request_kwargs
        )

        logger.info(f"Decrypting identity for DRP privacy request {privacy_request.id}")

        decrypted_identity: DrpIdentity = DrpIdentity(
            **jwt.decode(data.identity, jwt_key, algorithms=["HS256"])
        )

        mapped_identity: PrivacyRequestIdentity = DrpFidesopsMapper.map_identity(
            drp_identity=decrypted_identity
        )

        cache_data(privacy_request, policy, mapped_identity, None, data)

        PrivacyRequestRunner(
            cache=cache,
            privacy_request=privacy_request,
        ).submit()

        return PrivacyRequestDRPStatusResponse(
            request_id=privacy_request.id,
            received_at=privacy_request.requested_at,
            status=DrpFidesopsMapper.map_status(privacy_request.status),
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
        id=request_id,
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
