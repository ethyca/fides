from fastapi import Depends, HTTPException, Security
from fastapi.routing import APIRouter
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK

from fides.api.api import deps
from fides.api.models.privacy_request_redaction_patterns import (
    PrivacyRequestRedactionPatterns,
)
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.privacy_request_redaction_patterns import (
    PrivacyRequestRedactionPatternsRequest,
    PrivacyRequestRedactionPatternsResponse,
)
from fides.api.util.logger import Pii
from fides.common.api.scope_registry import (
    PRIVACY_REQUEST_REDACTION_PATTERNS_READ,
    PRIVACY_REQUEST_REDACTION_PATTERNS_UPDATE,
)
from fides.common.api.v1.urn_registry import (
    PRIVACY_REQUEST_REDACTION_PATTERNS,
    V1_URL_PREFIX,
)

router = APIRouter(
    tags=["Privacy Request Redaction Patterns"],
    prefix=V1_URL_PREFIX,
)


@router.get(
    PRIVACY_REQUEST_REDACTION_PATTERNS,
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestRedactionPatternsResponse,
    dependencies=[
        Security(verify_oauth_client, scopes=[PRIVACY_REQUEST_REDACTION_PATTERNS_READ])
    ],
)
def get_privacy_request_redaction_patterns(
    *, db: Session = Depends(deps.get_db)
) -> PrivacyRequestRedactionPatternsResponse:
    """
    Get the current privacy request redaction patterns configuration.

    Returns the list of regex patterns used to mask dataset, collection,
    and field names in privacy request package reports.
    """
    logger.info("Getting privacy request redaction patterns configuration")

    patterns = PrivacyRequestRedactionPatterns.get_patterns(db)
    return PrivacyRequestRedactionPatternsResponse(patterns=patterns)


@router.put(
    PRIVACY_REQUEST_REDACTION_PATTERNS,
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestRedactionPatternsResponse,
    dependencies=[
        Security(
            verify_oauth_client, scopes=[PRIVACY_REQUEST_REDACTION_PATTERNS_UPDATE]
        )
    ],
)
def update_privacy_request_redaction_patterns(
    *,
    db: Session = Depends(deps.get_db),
    request: PrivacyRequestRedactionPatternsRequest,
) -> PrivacyRequestRedactionPatternsResponse:
    """
    Update the privacy request redaction patterns configuration.

    This is a complete replacement of the patterns list. To clear all patterns,
    send an empty list.
    """
    logger.info(
        "Updating privacy request redaction patterns configuration with {} patterns",
        len(request.patterns),
    )

    try:
        # Create or update the patterns record
        patterns_record = PrivacyRequestRedactionPatterns.create_or_update(
            db=db, data={"patterns": request.patterns}
        )

        logger.info("Successfully updated privacy request redaction patterns")
        return PrivacyRequestRedactionPatternsResponse(
            patterns=patterns_record.patterns
        )

    except Exception as e:
        logger.error(
            "Failed to update privacy request redaction patterns: {}", Pii(str(e))
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update privacy request redaction patterns",
        ) from e
