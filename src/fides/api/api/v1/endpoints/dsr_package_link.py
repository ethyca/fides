import uuid

from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_302_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api.deps import get_db
from fides.api.common_exceptions import AuthenticationError, AuthorizationError
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.storage import get_active_default_storage_config
from fides.api.oauth.utils import validate_download_token
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.schemas.storage.storage import StorageType
from fides.api.service.storage.streaming.s3 import S3StorageClient
from fides.api.util.api_router import APIRouter
from fides.api.util.endpoint_utils import fides_limiter
from fides.common.api.v1.urn_registry import PRIVACY_CENTER_DSR_PACKAGE, V1_URL_PREFIX
from fides.config import CONFIG

router = APIRouter(tags=["Privacy Center"], prefix=V1_URL_PREFIX)


def get_privacy_request_or_error(
    privacy_request_id: str, db: Session
) -> PrivacyRequest:
    """Load the privacy request or throw a 404"""
    # Note: UUID format validation is now done earlier in the endpoint
    privacy_request = PrivacyRequest.get(db, object_id=privacy_request_id)

    if not privacy_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No privacy request found with id '{privacy_request_id}'.",
        )

    if privacy_request.deleted_at is not None:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Privacy request with id {privacy_request_id} has been deleted.",
        )

    return privacy_request


def raise_error(status_code: int, detail: str) -> None:
    """Raise an HTTPException with the given status code and detail"""
    raise HTTPException(
        status_code=status_code,
        detail=detail,
    )


@router.get(
    PRIVACY_CENTER_DSR_PACKAGE,
    status_code=HTTP_302_FOUND,
)
@fides_limiter.limit(CONFIG.security.public_request_rate_limit)
def get_access_results_urls(
    privacy_request_id: str,
    token: str,
    db: Session = Depends(get_db),
    *,
    request: Request,  # required for rate limiting
    response: Response,  # required for rate limiting
) -> RedirectResponse:
    """
    Public endpoint for retrieving access results URLs for a privacy request.
    This endpoint generates fresh presigned URLs and redirects to the first available result.
    This endpoint is designed to be accessible via email links sent to end users.
    No authentication is required, but a valid download token is required for security.
    Rate limiting is applied for additional security.

    privacy_request_id parameter is required in the URL path.
    token parameter is required as a query parameter for security.
    """
    # --------------Security checks--------------
    # First validate the privacy request ID format to prevent SSRF attacks
    # This is a simple string check that doesn't require database access
    if not privacy_request_id.startswith("pri_"):
        raise_error(
            HTTP_400_BAD_REQUEST,
            f"Invalid privacy request ID format: '{privacy_request_id}'. Must start with 'pri_' followed by a valid UUID v4.",
        )

    # Extract the UUID part after the prefix
    uuid_part = privacy_request_id[4:]  # Remove "pri_" prefix

    try:
        uuid.UUID(uuid_part, version=4)
    except ValueError:
        raise_error(
            HTTP_400_BAD_REQUEST,
            f"Invalid privacy request ID format: '{privacy_request_id}'. Must start with 'pri_' followed by a valid UUID v4.",
        )

    try:
        # Validate the download token before proceeding
        validate_download_token(token, privacy_request_id)
    except AuthenticationError as e:
        raise_error(HTTP_401_UNAUTHORIZED, str(e.detail))
    except AuthorizationError as e:
        raise_error(HTTP_403_FORBIDDEN, str(e.detail))

    # --------------Data checks--------------
    storage_config = get_active_default_storage_config(db)
    privacy_request = get_privacy_request_or_error(privacy_request_id, db)

    if not storage_config:
        raise_error(
            HTTP_400_BAD_REQUEST, "No active default storage configuration found."
        )

    if privacy_request.status != PrivacyRequestStatus.complete:
        raise_error(
            HTTP_400_BAD_REQUEST,
            f"Access results for privacy request '{privacy_request.id}' are not available because the request is not complete.",
        )

    if (
        not privacy_request.access_result_urls
        or not privacy_request.access_result_urls.get("access_result_urls")
    ):
        raise_error(
            HTTP_404_NOT_FOUND,
            f"No access results found for privacy request '{privacy_request.id}'.",
        )

    # --------------Processing--------------
    file_name = f"{privacy_request.id}.zip"

    # At this point, storage_config is guaranteed to exist due to earlier validation
    # and we've already checked that it's not None above
    assert storage_config is not None

    if storage_config.type != StorageType.s3:
        # Handle all other storage types (transcend, ethyca, local, etc.)
        raise_error(
            HTTP_400_BAD_REQUEST,
            f"Storage type '{storage_config.type}' is not supported for download redirects. "
            "Only S3 storage is supported for this endpoint.",
        )

    # Get bucket name from storage config
    bucket_name = storage_config.details.get("bucket")
    if not bucket_name:
        raise_error(HTTP_400_BAD_REQUEST, "S3 bucket name not found in storage config.")

    try:
        # Use S3StorageClient for cleaner presigned URL generation
        s3_storage_client = S3StorageClient(storage_config.secrets)
        result_url = s3_storage_client.generate_presigned_url(
            bucket=bucket_name,
            key=file_name,
        )
    except Exception as e:
        raise_error(HTTP_400_BAD_REQUEST, f"Failed to generate presigned URL: {str(e)}")

    # Convert the URL to string for RedirectResponse
    return RedirectResponse(url=str(result_url), status_code=HTTP_302_FOUND)
