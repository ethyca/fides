import ipaddress
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import Depends, HTTPException, Request, Response
from fastapi.params import Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from sqlalchemy import literal
from sqlalchemy.orm import Query, Session
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from fides.api.api.deps import get_db
from fides.api.api.v1.endpoints.consent_request_endpoints import (
    _get_consent_request_and_provided_identity,
)
from fides.api.api.v1.endpoints.privacy_request_endpoints import (
    create_privacy_request_func,
)
from fides.api.api.v1.endpoints.utils import (
    fides_limiter,
    validate_start_and_end_filters,
)
from fides.api.api.v1.scope_registry import (
    CURRENT_PRIVACY_PREFERENCE_READ,
    PRIVACY_PREFERENCE_HISTORY_READ,
)
from fides.api.api.v1.urn_registry import (
    CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY,
    CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID,
    CURRENT_PRIVACY_PREFERENCES_REPORT,
    HISTORICAL_PRIVACY_PREFERENCES_REPORT,
    PRIVACY_PREFERENCES,
    V1_URL_PREFIX,
)
from fides.api.ctl.database.seed import DEFAULT_CONSENT_POLICY
from fides.api.models.fides_user import FidesUser
from fides.api.models.privacy_experience import PrivacyExperienceHistory
from fides.api.models.privacy_notice import PrivacyNotice, PrivacyNoticeHistory
from fides.api.models.privacy_preference import (
    CurrentPrivacyPreference,
    PrivacyPreferenceHistory,
)
from fides.api.models.privacy_request import (
    ConsentRequest,
    PrivacyRequest,
    ProvidedIdentity,
    ProvidedIdentityType,
)
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.privacy_preference import (
    ConsentReportingSchema,
    CurrentPrivacyPreferenceReportingSchema,
    CurrentPrivacyPreferenceSchema,
    PrivacyPreferencesCreate,
    PrivacyPreferencesRequest,
)
from fides.api.schemas.privacy_request import (
    BulkPostPrivacyRequests,
    PrivacyRequestCreate,
    VerificationCode,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.util.api_router import APIRouter
from fides.api.util.consent_util import (
    get_or_create_fides_user_device_id_provided_identity,
)
from fides.core.config import CONFIG
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
    """Allows retrieving Current Privacy Preferences through the Privacy Center

    Verifies the verification code and retrieves CurrentPrivacyPreferences, which are the latest
    preferences saved for each PrivacyNotice
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

    # Fides user device id provided identities are saved in a different column from the
    # other provided identity types on privacy preference records
    field_name: str = (
        "fides_user_device_provided_identity_id"
        if provided_identity.field_name == ProvidedIdentityType.fides_user_device_id
        else "provided_identity_id"
    )

    logger.info("Getting current privacy preferences for verified provided identity")

    query = (
        db.query(CurrentPrivacyPreference)
        .filter_by(**{field_name: provided_identity.id})
        .order_by(CurrentPrivacyPreference.privacy_notice_id)
    )
    return paginate(query, params)


def verify_privacy_notice_and_historical_records(
    db: Session, data: PrivacyPreferencesRequest
) -> None:
    """
    Used when saving privacy preferences: runs a check that makes sure all the privacy notice histories referenced by
    the provided `preferences` exist in the database, and also makes sure the provided `preferences` do not specify
    the same privacy notice.

    For example, we want to avoid having two preferences saved for the same version of a *historical privacy notice*,
    or two preferences saved for different versions of the same *privacy notice*.
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


def extract_identity_from_provided_identity(
    identity: Optional[ProvidedIdentity], identity_type: ProvidedIdentityType
) -> Tuple[Optional[str], Optional[str]]:
    """Pull the identity data off of the ProvidedIdentity given that it's the correct type"""
    value: Optional[str] = None
    hashed_value: Optional[str] = None

    if identity and identity.encrypted_value and identity.field_name == identity_type:
        value = identity.encrypted_value["value"]
        hashed_value = identity.hashed_value

    return value, hashed_value


def anonymize_ip_address(ip_address: Optional[str]) -> Optional[str]:
    """Mask IP Address to be saved with the privacy preference
    - For ipv4, set last octet to 0
    - For ipv6, set last 80 of the 128 bits are set to zero.
    """
    if not ip_address:
        return None

    try:
        ip_object = ipaddress.ip_address(ip_address)

        if ip_object.version == 4:
            ipv4_network = ipaddress.IPv4Network(ip_address + "/24", strict=False)
            masked_ip_address = str(ipv4_network.network_address)
            return masked_ip_address.split("/", maxsplit=1)[0]

        if ip_object.version == 6:
            ipv6_network = ipaddress.IPv6Network(ip_address + "/48", strict=False)
            return str(ipv6_network.network_address.exploded)

        return None

    except ValueError:
        return None


def _get_request_origin_and_config(
    db: Session, data: PrivacyPreferencesRequest
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract details to save with the privacy preferences preferences from the
    Experience history if applicable: request origin (privacy center, overlay)
    and the Experience Config history.

    Additionally validate that the experience config history is valid if supplied.
    """
    privacy_experience_history: Optional[PrivacyExperienceHistory] = None
    experience_config_id: Optional[str] = None
    if data.privacy_experience_history_id:
        privacy_experience_history = PrivacyExperienceHistory.get(
            db=db, object_id=data.privacy_experience_history_id
        )
        if not privacy_experience_history:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Privacy Experience History '{data.privacy_experience_history_id}' not found.",
            )
        experience_config_id = privacy_experience_history.experience_config_history_id

    origin: Optional[str] = (
        privacy_experience_history.component.value  # type: ignore[attr-defined]
        if privacy_experience_history
        else None
    )
    return origin, experience_config_id


def supplement_privacy_preferences_with_user_and_experience_details(
    db: Session, request: Request, data: PrivacyPreferencesRequest
) -> PrivacyPreferencesCreate:
    """
    Pull additional user information from request headers and experience to record for consent reporting purposes

    """

    request_headers = request.headers
    ip_address: Optional[str] = request.client.host if request.client else None
    user_agent: Optional[str] = request_headers.get("User-Agent")
    url_recorded: Optional[str] = request_headers.get("Referer")
    request_origin, experience_config_history_id = _get_request_origin_and_config(
        db, data
    )

    return PrivacyPreferencesCreate(
        **data.dict(),
        anonymized_ip_address=anonymize_ip_address(ip_address),
        experience_config_history_id=experience_config_history_id,
        request_origin=request_origin,
        url_recorded=url_recorded,
        user_agent=user_agent,
    )


@router.patch(
    CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID,
    status_code=HTTP_200_OK,
    response_model=List[CurrentPrivacyPreferenceSchema],
)
def save_privacy_preferences_with_verified_identity(
    *,
    consent_request_id: str,
    db: Session = Depends(get_db),
    data: PrivacyPreferencesRequest,
    request: Request,
) -> List[CurrentPrivacyPreference]:
    """Saves privacy preferences in the privacy center.

    The ConsentRequest may have been created under an email, phone number, *or* fides user device id.
    Preferences can be saved under both an email *and* a fides user device id, if the email was persisted
    with the ConsentRequest and the fides user device id is passed in with this secondary request.

    Creates historical records for these preferences for record keeping, and also updates current preferences.
    Creates a privacy request to propagate preferences to third party systems.
    """
    verify_privacy_notice_and_historical_records(db=db, data=data)
    consent_request, provided_identity = _get_consent_request_and_provided_identity(
        db=db,
        consent_request_id=consent_request_id,
        verification_code=data.code,
    )
    if not provided_identity.hashed_value:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Provided identity missing"
        )

    if provided_identity.field_name == ProvidedIdentityType.fides_user_device_id:
        # If consent request was saved against a fides user device id only, this is our primary identity
        # This workflow is for when customers don't want to collect email/phone number.
        fides_user_provided_identity = provided_identity
        provided_identity = None  # type: ignore[assignment]
    else:
        # Get the fides user device id from the dictionary of browser identifiers
        try:
            fides_user_provided_identity = (
                get_or_create_fides_user_device_id_provided_identity(
                    db=db, identity_data=data.browser_identity
                )
            )
        except HTTPException:
            fides_user_provided_identity = None

    logger.info("Saving privacy preferences")
    return _save_privacy_preferences_for_identities(
        db=db,
        consent_request=consent_request,
        verified_provided_identity=provided_identity,
        fides_user_provided_identity=fides_user_provided_identity,
        request_data=supplement_privacy_preferences_with_user_and_experience_details(
            db, request, data
        ),
    )


def _save_privacy_preferences_for_identities(
    db: Session,
    consent_request: Optional[ConsentRequest],
    verified_provided_identity: Optional[ProvidedIdentity],
    fides_user_provided_identity: Optional[ProvidedIdentity],
    request_data: PrivacyPreferencesCreate,
) -> List[CurrentPrivacyPreference]:
    """
    Saves privacy preferences (both historical and current records) and creates a privacy request to propagate those
    preferences for when we have a verified user identity (like email/phone number), just a fides user device from
    the browser, or both.
    """
    created_historical_preferences: List[PrivacyPreferenceHistory] = []
    upserted_current_preferences: List[CurrentPrivacyPreference] = []

    email, hashed_email = extract_identity_from_provided_identity(
        verified_provided_identity, ProvidedIdentityType.email
    )
    phone_number, hashed_phone_number = extract_identity_from_provided_identity(
        verified_provided_identity, ProvidedIdentityType.phone_number
    )
    fides_user_device_id, hashed_device_id = extract_identity_from_provided_identity(
        fides_user_provided_identity, ProvidedIdentityType.fides_user_device_id
    )

    for privacy_preference in request_data.preferences:
        historical_preference: PrivacyPreferenceHistory = PrivacyPreferenceHistory.create(
            db=db,
            data={
                "anonymized_ip_address": request_data.anonymized_ip_address,
                "email": email,
                "privacy_experience_config_history_id": request_data.experience_config_history_id
                if request_data.experience_config_history_id
                else None,
                "privacy_experience_history_id": request_data.privacy_experience_history_id
                if request_data.privacy_experience_history_id
                else None,
                "fides_user_device": fides_user_device_id,
                "fides_user_device_provided_identity_id": fides_user_provided_identity.id
                if fides_user_provided_identity
                else None,
                "hashed_email": hashed_email,
                "hashed_fides_user_device": hashed_device_id,
                "hashed_phone_number": hashed_phone_number,
                "method": request_data.method,
                "phone_number": phone_number,
                "preference": privacy_preference.preference,
                "privacy_notice_history_id": privacy_preference.privacy_notice_history_id,
                "provided_identity_id": verified_provided_identity.id
                if verified_provided_identity
                else None,
                "request_origin": request_data.request_origin,
                "user_agent": request_data.user_agent,
                "user_geography": request_data.user_geography,
                "url_recorded": request_data.url_recorded,
            },
            check_name=False,
        )
        upserted_current_preference: CurrentPrivacyPreference = (
            historical_preference.current_privacy_preference
        )

        created_historical_preferences.append(historical_preference)
        upserted_current_preferences.append(upserted_current_preference)

    identity = (
        request_data.browser_identity if request_data.browser_identity else Identity()
    )
    if verified_provided_identity:
        # Pull the information on the ProvidedIdentity for the ConsentRequest to pass along to create a PrivacyRequest
        setattr(
            identity,
            verified_provided_identity.field_name.value,  # type:ignore[attr-defined]
            verified_provided_identity.encrypted_value["value"],  # type:ignore[index]
        )

    # Privacy Request needs to be created with respect to the *historical* privacy preferences
    privacy_request_results: BulkPostPrivacyRequests = create_privacy_request_func(
        db=db,
        config_proxy=ConfigProxy(db),
        data=[
            PrivacyRequestCreate(
                identity=identity,
                policy_key=request_data.policy_key or DEFAULT_CONSENT_POLICY,
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

    if consent_request:
        # If we have a verified user identity, go ahead and update the associated ConsentRequest for record keeping
        consent_request.privacy_request_id = privacy_request_results.succeeded[0].id
        consent_request.save(db=db)
    return upserted_current_preferences


@router.patch(
    PRIVACY_PREFERENCES,
    status_code=HTTP_200_OK,
    response_model=List[CurrentPrivacyPreferenceSchema],
)
@fides_limiter.limit(CONFIG.security.public_request_rate_limit)
def save_privacy_preferences(
    *,
    db: Session = Depends(get_db),
    data: PrivacyPreferencesRequest,
    request: Request,
    response: Response,  # required for rate limiting
) -> List[CurrentPrivacyPreference]:
    """Saves privacy preferences with respect to a fides user device id.

    Creates historical records for these preferences for record keeping, and also updates current preferences.
    Creates a privacy request to propagate preferences to third party systems.
    """
    verify_privacy_notice_and_historical_records(db=db, data=data)

    fides_user_provided_identity = get_or_create_fides_user_device_id_provided_identity(
        db=db, identity_data=data.browser_identity
    )

    logger.info("Saving privacy preferences with respect to fides user device id")
    return _save_privacy_preferences_for_identities(
        db=db,
        consent_request=None,
        verified_provided_identity=None,
        fides_user_provided_identity=fides_user_provided_identity,
        request_data=supplement_privacy_preferences_with_user_and_experience_details(
            db, request, data
        ),
    )


@router.get(
    CURRENT_PRIVACY_PREFERENCES_REPORT,
    status_code=HTTP_200_OK,
    dependencies=[
        Security(verify_oauth_client, scopes=[CURRENT_PRIVACY_PREFERENCE_READ])
    ],
    response_model=Page[CurrentPrivacyPreferenceReportingSchema],
)
def get_current_privacy_preferences_report(
    *,
    params: Params = Depends(),
    db: Session = Depends(get_db),
    updated_lt: Optional[datetime] = None,
    updated_gt: Optional[datetime] = None,
) -> AbstractPage[CurrentPrivacyPreference]:
    """Returns the most recently saved privacy preferences for a given privacy notice"""

    validate_start_and_end_filters([(updated_lt, updated_gt, "updated")])

    query: Query[CurrentPrivacyPreference] = db.query(CurrentPrivacyPreference)

    if updated_lt:
        query = query.filter(CurrentPrivacyPreference.updated_at < updated_lt)
    if updated_gt:
        query = query.filter(CurrentPrivacyPreference.updated_at > updated_gt)

    query = query.order_by(CurrentPrivacyPreference.updated_at.desc())

    return paginate(query, params)


@router.get(
    HISTORICAL_PRIVACY_PREFERENCES_REPORT,
    status_code=HTTP_200_OK,
    dependencies=[
        Security(verify_oauth_client, scopes=[PRIVACY_PREFERENCE_HISTORY_READ])
    ],
    response_model=Page[ConsentReportingSchema],
)
def get_historical_consent_report(
    *,
    params: Params = Depends(),
    db: Session = Depends(get_db),
    request_timestamp_gt: Optional[datetime] = None,
    request_timestamp_lt: Optional[datetime] = None,
) -> AbstractPage[PrivacyPreferenceHistory]:
    """Endpoint to return a historical record of all privacy preferences saved for consent reporting"""

    validate_start_and_end_filters(
        [(request_timestamp_lt, request_timestamp_gt, "request_timestamp")]
    )

    query: Query[PrivacyPreferenceHistory] = (
        db.query(
            PrivacyPreferenceHistory.id,
            PrivacyRequest.id.label("privacy_request_id"),
            PrivacyPreferenceHistory.email.label("email"),
            PrivacyPreferenceHistory.phone_number.label("phone_number"),
            PrivacyPreferenceHistory.fides_user_device.label("fides_user_device_id"),
            PrivacyPreferenceHistory.secondary_user_ids,
            PrivacyPreferenceHistory.created_at.label("request_timestamp"),
            PrivacyPreferenceHistory.request_origin.label("request_origin"),
            PrivacyRequest.status.label("request_status"),
            literal("consent").label(
                "request_type"
            ),  # Right now, we know this is consent, so hardcoding to avoid the Policy/Rule join
            FidesUser.username.label("approver_id"),
            PrivacyPreferenceHistory.privacy_notice_history_id.label(
                "privacy_notice_history_id"
            ),
            PrivacyPreferenceHistory.preference.label("preference"),
            PrivacyPreferenceHistory.user_geography.label("user_geography"),
            PrivacyPreferenceHistory.relevant_systems.label("relevant_systems"),
            PrivacyPreferenceHistory.affected_system_status.label(
                "affected_system_status"
            ),
            PrivacyPreferenceHistory.url_recorded.label("url_recorded"),
            PrivacyPreferenceHistory.user_agent.label("user_agent"),
            PrivacyPreferenceHistory.privacy_experience_history_id.label(
                "privacy_experience_history_id"
            ),
            PrivacyPreferenceHistory.privacy_experience_config_history_id.label(
                "experience_config_history_id"
            ),
            PrivacyPreferenceHistory.anonymized_ip_address.label(
                "truncated_ip_address"
            ),
            PrivacyPreferenceHistory.method.label("method"),
        )
        .outerjoin(
            PrivacyRequest,
            PrivacyRequest.id == PrivacyPreferenceHistory.privacy_request_id,
        )
        .outerjoin(FidesUser, PrivacyRequest.reviewed_by == FidesUser.id)
    )

    if request_timestamp_lt:
        query = query.filter(PrivacyPreferenceHistory.created_at < request_timestamp_lt)
    if request_timestamp_gt:
        query = query.filter(PrivacyPreferenceHistory.created_at > request_timestamp_gt)

    query = query.order_by(PrivacyPreferenceHistory.created_at.desc())

    return paginate(query, params)
