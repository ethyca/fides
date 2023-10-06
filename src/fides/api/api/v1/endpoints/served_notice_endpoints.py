from typing import Dict, List, Optional, Union

from fastapi import Depends, HTTPException, Request, Response
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK

from fides.api.api.deps import get_db
from fides.api.api.v1.endpoints.consent_request_endpoints import (
    _get_consent_request_and_provided_identity,
)
from fides.api.api.v1.endpoints.privacy_preference_endpoints import (
    classify_identity_type_for_privacy_center_consent_reporting,
    update_request_body_for_consent_served_or_saved,
    verify_privacy_notice_and_historical_records,
)
from fides.api.common_exceptions import (
    IdentityNotFoundException,
    PrivacyNoticeHistoryNotFound,
    SystemNotFound,
)
from fides.api.custom_types import SafeStr
from fides.api.models.privacy_preference import LastServedNotice, ServedNoticeHistory
from fides.api.models.privacy_request import ProvidedIdentity
from fides.api.schemas.privacy_preference import (
    LastServedConsentSchema,
    RecordConsentServedCreate,
    RecordConsentServedRequest,
)
from fides.api.util.api_router import APIRouter
from fides.api.util.consent_util import (
    get_or_create_fides_user_device_id_provided_identity,
)
from fides.api.util.endpoint_utils import fides_limiter
from fides.api.util.tcf.tcf_experience_contents import (
    TCF_SECTION_MAPPING,
    ConsentRecordType,
)
from fides.common.api.v1.urn_registry import (
    CONSENT_REQUEST_NOTICES_SERVED,
    NOTICES_SERVED,
    V1_URL_PREFIX,
)
from fides.config import CONFIG

router = APIRouter(tags=["Privacy Preference"], prefix=V1_URL_PREFIX)


def save_consent_served_for_identities(
    db: Session,
    verified_provided_identity: Optional[ProvidedIdentity],
    fides_user_provided_identity: Optional[ProvidedIdentity],
    request: Request,
    original_request_data: RecordConsentServedRequest,
) -> List[LastServedNotice]:
    """
    Shared method to save that consent components were served to the end user.

    Saves that either privacy notices or individual TCF components like purposes, special purposes, vendors,
    systems, special features, or features were served.

    We save a historical record every time a consent item was served to the user in the frontend,
    and a separate "last served notice" for just the last time a consent item was served to a given user.
    """
    upserted_last_served: List[LastServedNotice] = []

    # Combines user data from request body and request headers for consent reporting
    common_data: Dict = update_request_body_for_consent_served_or_saved(
        db=db,
        verified_provided_identity=verified_provided_identity,
        fides_user_provided_identity=fides_user_provided_identity,
        request=request,
        original_request_data=original_request_data,
        resource_type=RecordConsentServedCreate,
    )
    common_data["serving_component"] = original_request_data.serving_component

    def save_consent_served_for_field_name(
        identifiers: Optional[Union[List[SafeStr], List[int]]],
        field_name: Optional[ConsentRecordType],
    ) -> None:
        """Internal helper for creating a ServedNoticeHistory record for various types
        of consent components

        Loops through the list of all consent components of a given type and saves
        to the database that they were served.
        """
        if not field_name or not identifiers:
            return

        for identifier in identifiers:
            (
                _,
                current_served,
            ) = ServedNoticeHistory.save_served_notice_history_and_last_notice_served(
                db=db,
                data={
                    **common_data,
                    **{
                        "acknowledge_mode": original_request_data.acknowledge_mode,
                        field_name.value: identifier,
                    },
                },
                check_name=False,
            )
            upserted_last_served.append(current_served)

    # Save consent served for privacy notices if applicable
    save_consent_served_for_field_name(
        original_request_data.privacy_notice_history_ids,
        ConsentRecordType.privacy_notice_history_id,
    )

    # Save consent served for TCF components if applicable
    for tcf_component, database_column in TCF_SECTION_MAPPING.items():
        save_consent_served_for_field_name(
            getattr(original_request_data, tcf_component, None),
            database_column,
        )

    return upserted_last_served


@router.patch(
    NOTICES_SERVED,
    status_code=HTTP_200_OK,
    response_model=List[LastServedConsentSchema],
)
@fides_limiter.limit(CONFIG.security.public_request_rate_limit)
def save_consent_served_to_user(
    *,
    db: Session = Depends(get_db),
    data: RecordConsentServedRequest,
    request: Request,
    response: Response,  # required for rate limiting
) -> List[LastServedNotice]:
    """Records that consent was served to a user with a given fides user device id.
    Generally called by the banner or an overlay.

    All items that were served in the same experience should be included in this request body.
    """
    verify_privacy_notice_and_historical_records(
        db=db, notice_history_list=data.privacy_notice_history_ids
    )

    fides_user_provided_identity = get_or_create_fides_user_device_id_provided_identity(
        db=db, identity_data=data.browser_identity
    )

    logger.info("Recording consent served with respect to fides user device id")

    try:
        return save_consent_served_for_identities(
            db=db,
            verified_provided_identity=None,
            fides_user_provided_identity=fides_user_provided_identity,
            request=request,
            original_request_data=data,
        )
    except (
        IdentityNotFoundException,
        PrivacyNoticeHistoryNotFound,
        SystemNotFound,
    ) as exc:
        raise HTTPException(status_code=400, detail=exc.args[0])


@router.patch(
    CONSENT_REQUEST_NOTICES_SERVED,
    status_code=HTTP_200_OK,
    response_model=List[LastServedConsentSchema],
)
def save_consent_served_via_privacy_center(
    *,
    consent_request_id: str,
    db: Session = Depends(get_db),
    data: RecordConsentServedRequest,
    request: Request,
) -> List[LastServedNotice]:
    """Saves that consent was served via a verified identity flow (privacy center)

    Capable of saving that consent was served against a verified email/phone number and a fides user device id
    simultaneously.

    Creates a ServedNoticeHistory history record for every consent item in the request and upserts
    a LastServedNotice record.
    """
    verify_privacy_notice_and_historical_records(
        db=db,
        notice_history_list=data.privacy_notice_history_ids,
    )
    _, provided_identity = _get_consent_request_and_provided_identity(
        db=db,
        consent_request_id=consent_request_id,
        verification_code=data.code,
    )

    (
        provided_identity_verified,
        fides_user_provided_identity,
    ) = classify_identity_type_for_privacy_center_consent_reporting(
        db=db,
        provided_identity=provided_identity,
        browser_identity=data.browser_identity,
    )

    logger.info("Saving notices served for privacy center")

    try:
        return save_consent_served_for_identities(
            db=db,
            verified_provided_identity=provided_identity_verified,
            fides_user_provided_identity=fides_user_provided_identity,
            request=request,
            original_request_data=data,
        )
    except (
        IdentityNotFoundException,
        PrivacyNoticeHistoryNotFound,
        SystemNotFound,
    ) as exc:
        raise HTTPException(status_code=400, detail=exc.args[0])
