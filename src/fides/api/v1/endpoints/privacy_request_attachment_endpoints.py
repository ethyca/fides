"""Unauthenticated upload endpoint for data-subject-uploaded privacy request files.

Same trust level as privacy-request creation, protected by the public
request rate limit and a streaming size cap.  See
``fides.service.privacy_request.attachment_user_provided_service`` for the
lifecycle model.
"""

from fastapi import Depends, File, Header, HTTPException, Request, Response, UploadFile
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_413_CONTENT_TOO_LARGE,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from fides.api.deps import get_db
from fides.api.schemas.attachment import PrivacyRequestAttachment
from fides.api.util.api_router import APIRouter
from fides.api.util.rate_limit import fides_limiter
from fides.common.urn_registry import PRIVACY_REQUEST_ATTACHMENT, V1_URL_PREFIX
from fides.config import CONFIG
from fides.service.privacy_request.attachment_user_provided_service import (
    DEFAULT_MAX_SIZE_BYTES,
    UPLOAD_READ_CHUNK_BYTES,
    upload_attachment,
)

router = APIRouter(tags=["Privacy Requests"], prefix=V1_URL_PREFIX)


@router.post(
    PRIVACY_REQUEST_ATTACHMENT,
    response_model=PrivacyRequestAttachment,
)
@fides_limiter.limit(CONFIG.security.request_rate_limit)
def upload_privacy_request_attachment(
    *,
    request: Request,  # required for rate limiting
    response: Response,  # required for rate limiting
    file: UploadFile = File(...),
    content_length: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> PrivacyRequestAttachment:
    """Upload a file attachment for use in a custom privacy request field.

    Unauthenticated — same trust level as privacy-request creation. Protected
    by the public request rate limit, a ``Content-Length`` pre-check, and a
    streaming size cap so an attacker cannot buffer unbounded bodies into
    memory.

    Returns an attachment ``id`` to include in the custom field's ``value``
    list when submitting the privacy request:

        "value": ["<attachment id>"]

    File type is verified via magic byte inspection.

    Gated on ``CONFIG.execution.allow_custom_privacy_request_field_collection``
    — uploads only make sense when custom fields (the mechanism that
    references them) are themselves enabled.
    """
    if not CONFIG.execution.allow_custom_privacy_request_field_collection:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=(
                "File attachments are disabled because custom privacy "
                "request field collection is not enabled."
            ),
        )

    # Content-Length pre-check — reject oversize requests before reading any
    # body bytes. A hostile client can lie about Content-Length, so the
    # streaming check below still runs as the authoritative guard; this just
    # avoids buffering the body at all in the honest case.
    if content_length is not None and content_length > DEFAULT_MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=HTTP_413_CONTENT_TOO_LARGE,
            detail=(
                f"File exceeds maximum allowed size of {DEFAULT_MAX_SIZE_BYTES} bytes"
            ),
        )

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = file.file.read(UPLOAD_READ_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > DEFAULT_MAX_SIZE_BYTES:
            raise HTTPException(
                status_code=HTTP_413_CONTENT_TOO_LARGE,
                detail=(
                    f"File exceeds maximum allowed size of {DEFAULT_MAX_SIZE_BYTES} bytes"
                ),
            )
        chunks.append(chunk)

    file_data = b"".join(chunks)

    try:
        return upload_attachment(file_data=file_data, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))
    except RuntimeError as exc:
        # Log the internal reason but return a generic 503 to the public
        # caller — storage-misconfig details shouldn't leak to unauth users.
        logger.error("Attachment upload failed (misconfiguration): {}", exc)
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail="File attachments are temporarily unavailable.",
        )
