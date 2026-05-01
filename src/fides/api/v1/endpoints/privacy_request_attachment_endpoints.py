"""Unauthenticated upload endpoint for privacy-request file attachments."""

from fastapi import (
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
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
from fides.service.privacy_request_attachments.privacy_request_attachments_deps import (
    get_attachment_user_provided_service,
)
from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
    DisallowedFileTypeError,
    FileTooLargeError,
    StorageBucketNotConfiguredError,
    StorageNotConfiguredError,
)
from fides.service.privacy_request_attachments.privacy_request_attachments_service import (
    UPLOAD_READ_CHUNK_BYTES,
    AttachmentUserProvidedService,
    resolve_upload_constraints,
)

router = APIRouter(tags=["Privacy Requests"], prefix=V1_URL_PREFIX)


@router.post(
    PRIVACY_REQUEST_ATTACHMENT,
    response_model=PrivacyRequestAttachment,
)
@fides_limiter.limit(CONFIG.security.privacy_request_attachment_rate_limit)
def upload_privacy_request_attachment(
    *,
    request: Request,  # required for rate limiting
    response: Response,  # required for rate limiting
    file: UploadFile = File(...),
    property_id: str = Form(...),
    policy_key: str = Form(...),
    field_name: str = Form(...),
    content_length: int | None = Header(default=None),
    db: Session = Depends(get_db),
    service: AttachmentUserProvidedService = Depends(
        get_attachment_user_provided_service
    ),
) -> PrivacyRequestAttachment:
    """Upload a file attachment for a custom privacy request field. Returns
    an ``id`` to echo back in the field's ``value`` list.

    ``property_id``, ``policy_key``, and ``field_name`` are mandatory.
    All three are persisted on the resulting row so submission can verify
    the upload was made under the same
    ``(property, policy, field)`` triple it's being claimed under — the
    same triple submission itself uses to look up the field's config.

    Gated on ``allow_custom_privacy_request_field_collection`` and
    ``allow_custom_privacy_request_file_upload``."""
    if not (
        CONFIG.execution.allow_custom_privacy_request_field_collection
        and CONFIG.execution.allow_custom_privacy_request_file_upload
    ):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="File attachments are disabled.",
        )

    constraints = resolve_upload_constraints(
        db,
        property_id=property_id,
        policy_key=policy_key,
        field_name=field_name,
    )

    # Content-Length pre-check — clients can lie, so the streaming check
    # below is the authoritative guard.
    if content_length is not None and content_length > constraints.max_size_bytes:
        raise HTTPException(
            status_code=HTTP_413_CONTENT_TOO_LARGE,
            detail=(
                f"File exceeds maximum allowed size of {constraints.max_size_bytes} bytes"
            ),
        )

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = file.file.read(UPLOAD_READ_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > constraints.max_size_bytes:
            raise HTTPException(
                status_code=HTTP_413_CONTENT_TOO_LARGE,
                detail=(
                    f"File exceeds maximum allowed size of {constraints.max_size_bytes} bytes"
                ),
            )
        chunks.append(chunk)

    file_data = b"".join(chunks)

    try:
        result = service.upload_attachment(
            file_data=file_data,
            session=db,
            constraints=constraints,
            field_name=field_name,
            property_id=property_id,
            policy_key=policy_key,
        )
        db.commit()
        return result
    except FileTooLargeError as exc:
        raise HTTPException(status_code=HTTP_413_CONTENT_TOO_LARGE, detail=str(exc))
    except DisallowedFileTypeError as exc:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(exc))
    except (StorageNotConfiguredError, StorageBucketNotConfiguredError) as exc:
        # Log internal reason; return generic 503 to unauth callers.
        logger.error("Attachment upload failed (misconfiguration): {}", exc)
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail="File attachments are temporarily unavailable.",
        )
