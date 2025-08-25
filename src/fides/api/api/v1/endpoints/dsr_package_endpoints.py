from typing import Optional

from fastapi import Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

from fides.api.api import deps
from fides.api.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.schemas.base_class import FidesSchema
from fides.api.util.api_router import APIRouter
from fides.common.api.v1 import urn_registry as urls

router = APIRouter(tags=["DSR Package"], prefix=urls.V1_URL_PREFIX)


class DSRPackageLinkResponse(FidesSchema):
    """Schema for DSR package download link response"""

    download_url: str
    expires_at: Optional[str] = None
    request_id: Optional[str] = None


@router.get(
    "/dsr-package-link",
    status_code=HTTP_200_OK,
    response_model=DSRPackageLinkResponse,
)
def get_dsr_package_link(
    *,
    db: Session = Depends(deps.get_db),
    request_id: Optional[str] = Query(
        None, description="Privacy request ID to get package link for"
    ),
    email: Optional[str] = Query(
        None, description="Email to filter privacy requests by"
    ),
) -> DSRPackageLinkResponse:
    """
    Public endpoint to generate a download URL for a DSR (Data Subject Request) package.

    This endpoint generates signed URLs for downloading completed privacy request packages.
    No authentication required - this is a public endpoint.

    Args:
        request_id: Optional privacy request ID to get package for specific request
        email: Optional email to filter requests by

    Returns:
        DSRPackageLinkResponse containing the download URL and metadata

    Raises:
        400: If neither request_id nor email is provided
        404: If no matching privacy request or package is found
    """

    logger.info("DSR package link request received", request_id=request_id, email=email)

    # Validate input - at least one parameter required
    if not request_id and not email:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Either request_id or email parameter is required"
        )

    privacy_request: Optional[PrivacyRequest] = None

    # Look up privacy request by ID if provided
    if request_id:
        privacy_request = PrivacyRequest.get_by(
            db, field="id", value=request_id
        )
        if not privacy_request:
            logger.warning("Privacy request not found", request_id=request_id)
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Privacy request with ID '{request_id}' not found"
            )

    # Look up privacy request by email if provided and no request_id
    elif email:
        # Find the most recent completed privacy request for this email
        # This is a simplified lookup - in practice you might want more sophisticated logic
        from fides.api.models.provided_identity import ProvidedIdentity

        identity = ProvidedIdentity.filter(
            db,
            conditions=(
                ProvidedIdentity.hashed_value.in_(
                    ProvidedIdentity.hash_value_for_search(email)
                )
                & (ProvidedIdentity.privacy_request_id.isnot(None))
            ),
        ).first()

        if not identity or not identity.privacy_request_id:
            logger.warning("No privacy request found for email", email=email)
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"No privacy request found for email '{email}'"
            )

        privacy_request = PrivacyRequest.get_by(
            db, field="id", value=identity.privacy_request_id
        )

    if not privacy_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Privacy request not found"
        )

    # Check if request is complete
    if privacy_request.status != PrivacyRequestStatus.complete:
        logger.warning(
            "Privacy request not complete",
            request_id=privacy_request.id,
            status=privacy_request.status
        )
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Privacy request '{privacy_request.id}' is not complete. Current status: {privacy_request.status}"
        )

    # Check if access results are available
    if not privacy_request.access_result_urls or not privacy_request.access_result_urls.access_result_urls:
        logger.warning(
            "No access results available for privacy request",
            request_id=privacy_request.id
        )
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No download package available for privacy request '{privacy_request.id}'"
        )

    # Get the first download URL (in practice, you might want to handle multiple URLs differently)
    download_url = privacy_request.access_result_urls.access_result_urls[0]

    logger.info(
        "DSR package link generated successfully",
        request_id=privacy_request.id,
        has_download_url=bool(download_url)
    )

    # In a real implementation, you might want to:
    # 1. Generate a new signed URL with appropriate expiration
    # 2. Log the access for audit purposes
    # 3. Rate limit requests
    # 4. Add additional security checks

    return DSRPackageLinkResponse(
        download_url=download_url,
        expires_at=None,  # Could calculate expiration time if implementing signed URLs
        request_id=privacy_request.id,
    )
