from typing import Optional

from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_302_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

import fides.api.deps as deps
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.storage import StorageConfig, get_active_default_storage_config
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.storage.s3 import maybe_get_s3_client
from fides.api.util.api_router import APIRouter
from fides.api.util.endpoint_utils import fides_limiter
from fides.common.api.v1.urn_registry import PRIVACY_CENTER_DSR_PACKAGE, V1_URL_PREFIX
from fides.config import CONFIG

router = APIRouter(tags=["Privacy Center"], prefix=V1_URL_PREFIX)


def get_privacy_request_from_path(
    privacy_request_id: str, db: Session = Depends(deps.get_db)
) -> PrivacyRequest:
    """Load the privacy request or throw a 404"""
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


@router.get(
    PRIVACY_CENTER_DSR_PACKAGE,
    status_code=HTTP_302_FOUND,
)
@fides_limiter.limit(CONFIG.security.public_request_rate_limit)
def get_access_results_urls(
    privacy_request: PrivacyRequest = Depends(get_privacy_request_from_path),
    storage_config: StorageConfig = Depends(get_active_default_storage_config),
    *,
    request: Request,  # required for rate limiting
    response: Response,  # required for rate limiting
) -> RedirectResponse:
    """
    Public endpoint for retrieving access results URLs for a privacy request.
    This endpoint generates fresh presigned URLs and redirects to the first available result.
    This endpoint is designed to be accessible via email links sent to end users.
    No authentication is required, but rate limiting is applied for security.

    privacy_request_id parameter is required in the URL path.
    """

    if privacy_request.status != PrivacyRequestStatus.complete:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Access results for privacy request '{privacy_request.id}' are not available because the request is not complete.",
        )

    if not privacy_request.access_result_urls:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No access results found for this privacy request.",
        )

    # Get the first access result URL from the existing URLs
    access_result_urls = privacy_request.access_result_urls.get(
        "access_result_urls", []
    )
    if not access_result_urls:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No access result URLs found for this privacy request.",
        )

    # Get the first access result URL from the existing URLs
    file_name = f"{privacy_request.id}.zip"
    if storage_config.type == "s3":
        s3_client = maybe_get_s3_client(
            auth_method=storage_config.details.get("auth_method"),
            storage_secrets=storage_config.details.get("storage_secrets"),
        )
        if not s3_client:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Failed to get S3 client.",
            )

        # Generate presigned URL directly using boto3
        bucket_name = storage_config.details.get("bucket")
        if not bucket_name:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="S3 bucket name not found in storage config.",
            )

        try:
            result_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": file_name},
                ExpiresIn=3600,  # 1 hour expiration
            )
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Failed to generate presigned URL: {str(e)}",
            )

        return RedirectResponse(url=result_url, status_code=HTTP_302_FOUND)
    if storage_config.type == "gcs":
        # GCS is not supported for this endpoint
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=(
                "Only S3 storage is supported for download redirects. "
                "Please contact support if you need to download access results from a different storage provider."
            ),
        )
    # Unsupported storage type
    raise HTTPException(
        status_code=HTTP_400_BAD_REQUEST,
        detail=f"Storage type '{storage_config.type}' is not supported for download redirects.",
    )
