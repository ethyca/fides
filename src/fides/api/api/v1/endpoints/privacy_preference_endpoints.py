import ipaddress
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Type, Union

from fastapi import Depends, HTTPException, Request
from fastapi.params import Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import literal
from sqlalchemy.orm import Query, Session
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from fides.api.api.deps import get_db
from fides.api.custom_types import SafeStr
from fides.api.models.fides_user import FidesUser
from fides.api.models.privacy_experience import PrivacyExperience
from fides.api.models.privacy_notice import PrivacyNotice, PrivacyNoticeHistory
from fides.api.models.privacy_preference import (
    CurrentPrivacyPreference,
    PrivacyPreferenceHistory,
    RequestOrigin,
)
from fides.api.models.privacy_request import (
    PrivacyRequest,
    ProvidedIdentity,
    ProvidedIdentityType,
)
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.privacy_preference import (
    ConsentReportingSchema,
    CurrentPrivacyPreferenceReportingSchema,
    PrivacyPreferencesCreate,
    PrivacyPreferencesRequest,
    RecordConsentServedCreate,
    RecordConsentServedRequest,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.util.api_router import APIRouter
from fides.api.util.consent_util import (
    get_or_create_fides_user_device_id_provided_identity,
)
from fides.api.util.endpoint_utils import validate_start_and_end_filters
from fides.common.api.scope_registry import (
    CURRENT_PRIVACY_PREFERENCE_READ,
    PRIVACY_PREFERENCE_HISTORY_READ,
)
from fides.common.api.v1.urn_registry import (
    CURRENT_PRIVACY_PREFERENCES_REPORT,
    HISTORICAL_PRIVACY_PREFERENCES_REPORT,
    V1_URL_PREFIX,
)

router = APIRouter(tags=["Privacy Preference"], prefix=V1_URL_PREFIX)


def verify_privacy_notice_and_historical_records(
    db: Session, notice_history_list: List[SafeStr]
) -> None:
    """
    Runs validation prior to saving privacy preferences with respect to notices.

    Ensures that all the privacy notice histories referenced by the provided `preferences` exist in the
    database, and that the provided `preferences` do not specify the same privacy notice.

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
            PrivacyNoticeHistory.id.in_(notice_history_list),
        )
        .distinct()
        .count()
    )

    if privacy_notice_count < len(notice_history_list):
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


def _supplement_request_data_from_request_headers(
    db: Session,
    request: Request,
    data: Union[PrivacyPreferencesRequest, RecordConsentServedRequest],
    resource_type: Union[
        Type[PrivacyPreferencesCreate], Type[RecordConsentServedCreate]
    ],
) -> Union[PrivacyPreferencesCreate, RecordConsentServedCreate]:
    """
    Supplement the request body with information pulled from the request headers and the
    experience itself to save for consent reporting purposes.
    """

    def get_request_origin_and_config() -> Tuple[Optional[str], Optional[str]]:
        """
        Extract user details from request headers and request body to save for consent
        reporting where applicable: request origin (privacy center, overlay, tcf_overlay)
        and the Experience Config history.

        Additionally validate that the experience config history is valid if supplied.
        """
        privacy_experience: Optional[PrivacyExperience] = None
        experience_config_history_identifier: Optional[str] = None
        if data.privacy_experience_id:
            privacy_experience = PrivacyExperience.get(
                db=db, object_id=data.privacy_experience_id
            )
            if not privacy_experience:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"Privacy Experience '{data.privacy_experience_id}' not found.",
                )
            experience_config_id = privacy_experience.experience_config_id
            if experience_config_id:
                experience_config_history_identifier = (
                    privacy_experience.experience_config.experience_config_history_id
                )

        origin: Optional[str] = (
            privacy_experience.component.value  # type: ignore[attr-defined]
            if privacy_experience
            else None
        )
        return origin, experience_config_history_identifier

    request_headers = request.headers

    ip_address: Optional[str] = get_ip_address(request)
    user_agent: Optional[str] = request_headers.get("User-Agent")
    url_recorded: Optional[str] = request_headers.get("Referer")
    request_origin, experience_config_history_id = get_request_origin_and_config()

    return resource_type(
        **data.dict(),
        anonymized_ip_address=anonymize_ip_address(ip_address),
        experience_config_history_id=experience_config_history_id,
        request_origin=request_origin,
        url_recorded=url_recorded,
        user_agent=user_agent,
    )


def get_ip_address(request: Request) -> Optional[str]:
    """Get client ip, preferring x-forwarded-for if it exists, otherwise, dropping back to
    request.client.host"""
    x_forwarded_for = (
        request.headers.get("x-forwarded-for") if request.headers else None
    )

    client_ip: Optional[str] = None
    if x_forwarded_for:
        try:
            client_ip = x_forwarded_for.split(",")[0].strip()
        except AttributeError:
            pass

    if not client_ip:
        client_ip = request.client.host if request.client else None

    return client_ip


def update_request_body_for_consent_served_or_saved(
    db: Session,
    verified_provided_identity: Optional[ProvidedIdentity],
    fides_user_provided_identity: Optional[ProvidedIdentity],
    request: Request,
    original_request_data: Union[PrivacyPreferencesRequest, RecordConsentServedRequest],
    resource_type: Union[
        Type[PrivacyPreferencesCreate], Type[RecordConsentServedCreate]
    ],
) -> Dict[str, Union[Optional[RequestOrigin], Optional[str]]]:
    """Common method for building the starting details to save that consent
    was served or saved for a given user for consent reporting purposes"""

    request_data: Union[
        PrivacyPreferencesCreate, RecordConsentServedCreate
    ] = _supplement_request_data_from_request_headers(
        db, request, original_request_data, resource_type=resource_type
    )

    email, hashed_email = extract_identity_from_provided_identity(
        verified_provided_identity, ProvidedIdentityType.email
    )
    phone_number, hashed_phone_number = extract_identity_from_provided_identity(
        verified_provided_identity, ProvidedIdentityType.phone_number
    )
    fides_user_device_id, hashed_device_id = extract_identity_from_provided_identity(
        fides_user_provided_identity, ProvidedIdentityType.fides_user_device_id
    )
    return {
        "anonymized_ip_address": request_data.anonymized_ip_address,
        "email": email,
        "privacy_experience_config_history_id": request_data.experience_config_history_id
        if request_data.experience_config_history_id
        else None,
        "privacy_experience_id": request_data.privacy_experience_id
        if request_data.privacy_experience_id
        else None,
        "fides_user_device": fides_user_device_id,
        "fides_user_device_provided_identity_id": fides_user_provided_identity.id
        if fides_user_provided_identity
        else None,
        "hashed_email": hashed_email,
        "hashed_fides_user_device": hashed_device_id,
        "hashed_phone_number": hashed_phone_number,
        "phone_number": phone_number,
        "provided_identity_id": verified_provided_identity.id
        if verified_provided_identity
        else None,
        "request_origin": request_data.request_origin,
        "user_agent": request_data.user_agent,
        "user_geography": request_data.user_geography,
        "url_recorded": request_data.url_recorded,
    }


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
    """Returns the most recently saved privacy preferences for a particular consent item"""

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
            PrivacyPreferenceHistory.privacy_experience_id.label(
                "privacy_experience_id"
            ),
            PrivacyPreferenceHistory.privacy_experience_config_history_id.label(
                "experience_config_history_id"
            ),
            PrivacyPreferenceHistory.anonymized_ip_address.label(
                "truncated_ip_address"
            ),
            PrivacyPreferenceHistory.method.label("method"),
            PrivacyPreferenceHistory.served_notice_history_id.label(
                "served_notice_history_id"
            ),
            PrivacyPreferenceHistory.purpose_consent.label("purpose_consent"),
            PrivacyPreferenceHistory.purpose_legitimate_interests.label(
                "purpose_legitimate_interests"
            ),
            PrivacyPreferenceHistory.special_purpose.label("special_purpose"),
            PrivacyPreferenceHistory.vendor_consent.label("vendor_consent"),
            PrivacyPreferenceHistory.vendor_legitimate_interests.label(
                "vendor_legitimate_interests"
            ),
            PrivacyPreferenceHistory.system_consent.label("system_consent"),
            PrivacyPreferenceHistory.system_legitimate_interests.label(
                "system_legitimate_interests"
            ),
            PrivacyPreferenceHistory.feature.label("feature"),
            PrivacyPreferenceHistory.special_feature.label("special_feature"),
            PrivacyPreferenceHistory.tcf_version.label("tcf_version"),
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


def classify_identity_type_for_privacy_center_consent_reporting(
    db: Session,
    provided_identity: ProvidedIdentity,
    browser_identity: Identity,
) -> Tuple[Optional[ProvidedIdentity], Optional[ProvidedIdentity]]:
    """Distinguish the type of identity we have for the user for consent reporting purposes.

    We want to classify the "provided_identity" as an identifier saved against an email or phone,
    and the "fides_user_provided_identity" as an identifier saved against the fides user device id.
    """
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
                    db=db, identity_data=browser_identity
                )
            )
        except HTTPException:
            fides_user_provided_identity = None

    return provided_identity, fides_user_provided_identity
