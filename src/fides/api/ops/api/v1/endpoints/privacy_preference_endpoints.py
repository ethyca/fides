from __future__ import annotations

from typing import List

from fastapi import Depends, HTTPException
from fastapi_pagination import Page, Params, paginate
from fastapi_pagination.bases import AbstractPage
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from fides.api.ctl.database.seed import DEFAULT_CONSENT_POLICY
from fides.api.ops.api.deps import get_db
from fides.api.ops.api.v1.endpoints.consent_request_endpoints import (
    _get_consent_request_and_provided_identity,
)
from fides.api.ops.api.v1.endpoints.privacy_request_endpoints import (
    create_privacy_request_func,
)
from fides.api.ops.api.v1.urn_registry import (
    CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY,
    CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID,
    V1_URL_PREFIX,
)
from fides.api.ops.common_exceptions import PrivacyNoticeHistoryNotFound
from fides.api.ops.models.privacy_notice import PrivacyNotice, PrivacyNoticeHistory
from fides.api.ops.models.privacy_preference import (
    CurrentPrivacyPreference,
    PrivacyPreferenceHistory,
)
from fides.api.ops.models.privacy_request import ProvidedIdentity, ProvidedIdentityType
from fides.api.ops.schemas.privacy_preference import (
    CurrentPrivacyPreferenceSchema,
    PrivacyPreferencesCreateWithCode,
)
from fides.api.ops.schemas.privacy_request import (
    BulkPostPrivacyRequests,
    PrivacyRequestCreate,
    VerificationCode,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.util.api_router import APIRouter
from fides.core.config.config_proxy import ConfigProxy

router = APIRouter(tags=["Privacy Preference"], prefix=V1_URL_PREFIX)


@router.post(
    CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY,
    status_code=HTTP_200_OK,
    response_model=Page[CurrentPrivacyPreferenceSchema],
)
def consent_request_verify_for_privacy_preferences(
    *,
    consent_request_id: str,
    params: Params = Depends(),
    db: Session = Depends(get_db),
    data: VerificationCode,
) -> AbstractPage[CurrentPrivacyPreference]:
    """Verifies the verification code and returns the CurrentPrivacyPreferences if successful.
    These are just the latest preferences saved for each PrivacyNotice.
    """
    _, provided_identity = _get_consent_request_and_provided_identity(
        db=db,
        consent_request_id=consent_request_id,
        verification_code=data.code,
    )

    if not provided_identity.hashed_value:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Provided identity missing"
        )

    logger.info("Getting current privacy preferences for verified provided identity")

    query = (
        db.query(CurrentPrivacyPreference)
        .join(
            ProvidedIdentity,
            provided_identity.id == CurrentPrivacyPreference.provided_identity_id,
        )
        .order_by(CurrentPrivacyPreference.privacy_notice_id)
        .all()
    )
    return paginate(query, params)


def verify_no_duplicated_privacy_notices(
    db: Session, data: PrivacyPreferencesCreateWithCode
) -> None:
    """
    Runs a check that largely makes sure no preferences are specified for the same privacy notice when
    saving privacy preferences.

    For example, we want to avoid having two preferences saved for the same version of a *historical privacy notice*,
    or two preferences saved for different versions of the same *privacy notice*.  This would also fail if the
    historical privacy notice didn't exist.
    """
    privacy_notice_count: int = (
        db.query(PrivacyNotice)
        .join(
            PrivacyNoticeHistory,
            PrivacyNoticeHistory.privacy_notice_id == PrivacyNotice.id,
        )
        .filter(
            PrivacyNoticeHistory.id.in_(
                [
                    consent_option.privacy_notice_history_id
                    for consent_option in data.preferences
                ]
            ),
        )
        .distinct()
        .count()
    )

    if privacy_notice_count < len(data.preferences):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid privacy notice histories in request",
        )


@router.patch(
    CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID,
    status_code=HTTP_200_OK,
    response_model=List[CurrentPrivacyPreferenceSchema],
)
def save_privacy_preferences(
    *,
    consent_request_id: str,
    db: Session = Depends(get_db),
    data: PrivacyPreferencesCreateWithCode,
) -> List[CurrentPrivacyPreference]:
    """Verifies the verification code and saves the user's privacy preferences if successful.

    Creates a historical record for each privacy preference for record keeping and then upserts the current preference
    for each privacy notice.  Creates a Privacy Request linked to the historical preferences to
    propagate these preferences where applicable.

    This workflow is for users saving preferences for privacy notices with a verified identity.
    """
    verify_no_duplicated_privacy_notices(db=db, data=data)
    consent_request, provided_identity = _get_consent_request_and_provided_identity(
        db=db,
        consent_request_id=consent_request_id,
        verification_code=data.code,
    )
    if not provided_identity.hashed_value:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Provided identity missing"
        )

    logger.info("Saving privacy preferences")
    created_historical_preferences: List[PrivacyPreferenceHistory] = []
    upserted_current_preferences: List[CurrentPrivacyPreference] = []
    for privacy_preference in data.preferences:
        try:
            historical_preference: PrivacyPreferenceHistory = PrivacyPreferenceHistory.create(
                db=db,
                data={
                    "email": provided_identity.encrypted_value["value"]
                    if provided_identity.field_name == ProvidedIdentityType.email
                    and provided_identity.encrypted_value
                    else None,
                    "phone_number": provided_identity.encrypted_value["value"]
                    if provided_identity.field_name == ProvidedIdentityType.phone_number
                    and provided_identity.encrypted_value
                    else None,
                    "preference": privacy_preference.preference,
                    "privacy_notice_history_id": privacy_preference.privacy_notice_history_id,
                    "provided_identity_id": provided_identity.id,
                    "request_origin": data.request_origin,
                    "secondary_user_ids": {
                        label: value for label, value in data.browser_identity if value
                    },
                    "user_agent": data.user_agent,
                    "user_geography": data.user_geography,
                    "url_recorded": data.url_recorded,
                },
                check_name=False,
            )
            upserted_current_preference: CurrentPrivacyPreference = (
                historical_preference.current_privacy_preference
            )
        except PrivacyNoticeHistoryNotFound:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"No Privacy Notice History record with id '{privacy_preference.privacy_notice_history_id}'",
            )

        created_historical_preferences.append(historical_preference)
        upserted_current_preferences.append(upserted_current_preference)

    identity = data.browser_identity if data.browser_identity else Identity()
    setattr(
        identity,
        provided_identity.field_name.value,  # type:ignore[attr-defined]
        provided_identity.encrypted_value["value"],  # type:ignore[index]
    )  # Pull the information on the ProvidedIdentity for the ConsentRequest to pass along to create a PrivacyRequest

    # Privacy Request needs to be created with respect to the *historical* privacy preferences
    privacy_request_results: BulkPostPrivacyRequests = create_privacy_request_func(
        db=db,
        config_proxy=ConfigProxy(db),
        data=[
            PrivacyRequestCreate(
                identity=identity,
                policy_key=data.policy_key or DEFAULT_CONSENT_POLICY,
            )
        ],
        authenticated=True,
        privacy_preferences=created_historical_preferences,
    )

    if privacy_request_results.failed or not privacy_request_results.succeeded:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=privacy_request_results.failed[0].message,
        )

    consent_request.privacy_request_id = privacy_request_results.succeeded[0].id
    consent_request.save(db=db)

    return upserted_current_preferences
