import ipaddress
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Type, Union

from fastapi import Depends, HTTPException, Request, Response
from fastapi.params import Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from sqlalchemy import literal
from sqlalchemy.orm import Query, Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api.deps import get_db
from fides.api.api.v1.endpoints.consent_request_endpoints import (
    _get_consent_request_and_provided_identity,
)
from fides.api.api.v1.endpoints.privacy_request_endpoints import (
    create_privacy_request_func,
)
from fides.api.common_exceptions import (
    DecodeFidesStringError,
    IdentityNotFoundException,
    PrivacyNoticeHistoryNotFound,
    SystemNotFound,
)
from fides.api.custom_types import SafeStr
from fides.api.db.seed import DEFAULT_CONSENT_POLICY
from fides.api.models.fides_user import FidesUser
from fides.api.models.privacy_experience import PrivacyExperience
from fides.api.models.privacy_notice import (
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeHistory,
)
from fides.api.models.privacy_preference import (
    CurrentPrivacyPreference,
    PrivacyPreferenceHistory,
    RequestOrigin,
    ServedNoticeHistory,
)
from fides.api.models.privacy_request import (
    ConsentRequest,
    PrivacyRequest,
    ProvidedIdentity,
    ProvidedIdentityType,
)
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.privacy_preference import (
    TCF_PREFERENCES_FIELD_MAPPING,
    ConsentOptionCreate,
    ConsentReportingSchema,
    CurrentPrivacyPreferenceReportingSchema,
    CurrentPrivacyPreferenceSchema,
    FidesStringFidesPreferences,
    PrivacyPreferencesCreate,
    PrivacyPreferencesRequest,
    RecordConsentServedCreate,
    RecordConsentServedRequest,
    SavePrivacyPreferencesResponse,
)
from fides.api.schemas.privacy_request import (
    BulkPostPrivacyRequests,
    PrivacyRequestCreate,
    VerificationCode,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.schemas.tcf import (
    TCFFeatureSave,
    TCFPurposeSave,
    TCFSpecialFeatureSave,
    TCFSpecialPurposeSave,
    TCFVendorSave,
)
from fides.api.util.api_router import APIRouter
from fides.api.util.consent_util import (
    get_or_create_fides_user_device_id_provided_identity,
)
from fides.api.util.endpoint_utils import fides_limiter, validate_start_and_end_filters
from fides.api.util.tcf.ac_string import decode_ac_string_to_preferences
from fides.api.util.tcf.fides_string import split_fides_string
from fides.api.util.tcf.tc_mobile_data import convert_fides_str_to_mobile_data
from fides.api.util.tcf.tc_string import decode_tc_string_to_preferences
from fides.api.util.tcf.tcf_experience_contents import (
    TCFExperienceContents,
    get_tcf_contents,
)
from fides.common.api.scope_registry import (
    CURRENT_PRIVACY_PREFERENCE_READ,
    PRIVACY_PREFERENCE_HISTORY_READ,
)
from fides.common.api.v1.urn_registry import (
    CONSENT_REQUEST_PRIVACY_PREFERENCES_VERIFY,
    CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID,
    CURRENT_PRIVACY_PREFERENCES_REPORT,
    HISTORICAL_PRIVACY_PREFERENCES_REPORT,
    PRIVACY_PREFERENCES,
    V1_URL_PREFIX,
)
from fides.config import CONFIG
from fides.config.config_proxy import ConfigProxy

router = APIRouter(tags=["Privacy Preference"], prefix=V1_URL_PREFIX)


def get_served_notice_history(
    db: Session, served_notice_history_id: str
) -> ServedNoticeHistory:
    """
    Helper method to load a ServedNoticeHistory record or throw a 404

    This tracks where a notice or tcf component was served.
    """
    logger.info("Finding ServedNoticeHistory with id '{}'", served_notice_history_id)
    served_notice_history = ServedNoticeHistory.get(
        db=db, object_id=served_notice_history_id
    )
    if not served_notice_history:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No ServedNoticeHistory record found for id {served_notice_history_id}.",
        )

    return served_notice_history


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
    """Retrieves the most recently saved privacy preferences through the Privacy Center

    Verifies the verification code and retrieves CurrentPrivacyPreferences, which are the latest
    preferences saved for each PrivacyNotice or TCF component
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
        .order_by(CurrentPrivacyPreference.created_at)
    )

    if not CONFIG.consent.tcf_enabled:
        query = query.filter(CurrentPrivacyPreference.privacy_notice_id.isnot(None))

    return paginate(query, params)


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
    ip_address: Optional[str] = request.client.host if request.client else None
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


@router.patch(
    CONSENT_REQUEST_PRIVACY_PREFERENCES_WITH_ID,
    status_code=HTTP_200_OK,
    response_model=SavePrivacyPreferencesResponse,
)
def save_privacy_preferences_with_verified_identity(
    *,
    consent_request_id: str,
    db: Session = Depends(get_db),
    data: PrivacyPreferencesRequest,
    request: Request,
) -> SavePrivacyPreferencesResponse:
    """Saves privacy preferences in the privacy center.

    The ConsentRequest may have been created under an email, phone number, *or* fides user device id.
    Preferences can be saved under both an email *and* a fides user device id, if the email was persisted
    with the ConsentRequest and the fides user device id is passed in with this secondary request.

    Creates historical records for these preferences for record keeping, and also updates current preferences.
    Creates a privacy request to propagate preferences to third party systems where applicable.
    """
    fides_string: Optional[str] = data.fides_string
    data = update_request_with_decoded_fides_string_fields(data, db)

    verify_privacy_notice_and_historical_records(
        db=db,
        notice_history_list=[
            consent_option.privacy_notice_history_id
            for consent_option in data.preferences
        ],
    )
    verify_previously_served_records(db, data)

    consent_request, provided_identity = _get_consent_request_and_provided_identity(
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

    logger.info("Saving privacy preferences")

    try:
        saved_preferences_response: SavePrivacyPreferencesResponse = (
            save_privacy_preferences_for_identities(
                db=db,
                consent_request=consent_request,
                verified_provided_identity=provided_identity_verified,
                fides_user_provided_identity=fides_user_provided_identity,
                request=request,
                original_request_data=data,
            )
        )
        saved_preferences_response.fides_mobile_data = convert_fides_str_to_mobile_data(
            fides_string
        )

        return saved_preferences_response

    except (
        IdentityNotFoundException,
        PrivacyNoticeHistoryNotFound,
        SystemNotFound,
        DecodeFidesStringError,
    ) as exc:
        raise HTTPException(status_code=400, detail=exc.args[0])


def persist_tcf_preferences(
    db: Session,
    user_data: Dict[str, str],
    request_data: PrivacyPreferencesRequest,
    saved_preferences_response: SavePrivacyPreferencesResponse,
) -> None:
    """Save TCF preferences with respect to individual TCF components if applicable.

    All TCF Preferences have frontend-only enforcement at the moment, so no Privacy Requests
    are created to propagate consent. The "upserted_current_preferences" list is updated in place.
    """
    if not CONFIG.consent.tcf_enabled:
        return

    def save_tcf_preference(
        component_type: str,
        preference_request: Union[
            TCFPurposeSave,
            TCFSpecialPurposeSave,
            TCFVendorSave,
            TCFFeatureSave,
            TCFSpecialFeatureSave,
        ],
    ) -> CurrentPrivacyPreference:
        """Internal helper method for dynamically saving a preference against a specific TCF component
        in the database where applicable

        Currently, we don't attempt to propagate these preferences to third party systems.
        """
        (
            _,
            current_preference,
        ) = PrivacyPreferenceHistory.create_history_and_upsert_current_preference(
            db=db,
            data={
                **user_data,
                **{
                    "preference": preference_request.preference,
                    component_type: preference_request.id,
                    "served_notice_history_id": preference_request.served_notice_history_id,
                },
            },
            check_name=False,
        )
        return current_preference

    # If applicable, loop through all the lists of TCF components and save each preference individually: with respect
    # to purposes, special purposes, vendors, features, special features, and/or systems.
    for tcf_preference_field, field_name in TCF_PREFERENCES_FIELD_MAPPING.items():
        # If no preferences were saved for this TCF component, this will be an empty
        # list, and nothing will be saved to the db.
        saved_preferences: List[
            Union[
                TCFPurposeSave,
                TCFSpecialPurposeSave,
                TCFVendorSave,
                TCFFeatureSave,
                TCFSpecialFeatureSave,
            ]
        ] = getattr(request_data, tcf_preference_field)

        for preference in saved_preferences:
            saved_section: List = getattr(
                saved_preferences_response, tcf_preference_field
            )
            saved_section.append(
                save_tcf_preference(
                    preference_request=preference,
                    component_type=field_name,
                )
            )


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


def save_privacy_preferences_for_identities(
    db: Session,
    consent_request: Optional[ConsentRequest],
    verified_provided_identity: Optional[ProvidedIdentity],
    fides_user_provided_identity: Optional[ProvidedIdentity],
    request: Request,
    original_request_data: PrivacyPreferencesRequest,
) -> SavePrivacyPreferencesResponse:
    """
    Shared method to save privacy preferences for an end user.

    Saves preferences for either a privacy notice, or individual TCF items like purposes, special purposes, vendors,
    systems, features, or special features.

    Creates both a detailed historical record and upserts a separate current record with just the most recently
    saved changes for each preference type.

    Creates a privacy request to propagate preferences to third-party systems if applicable.
    """
    created_historical_preferences: List[PrivacyPreferenceHistory] = []
    saved_preferences_response = SavePrivacyPreferencesResponse()

    # Combines user data from request body and request headers for consent reporting
    common_user_data: Dict = update_request_body_for_consent_served_or_saved(
        db=db,
        verified_provided_identity=verified_provided_identity,
        fides_user_provided_identity=fides_user_provided_identity,
        request=request,
        original_request_data=original_request_data,
        resource_type=PrivacyPreferencesCreate,
    )
    common_user_data["method"] = original_request_data.method

    # Persists preferences with respect to individual TCF attributes first if applicable
    persist_tcf_preferences(
        db=db,
        user_data=common_user_data,
        request_data=original_request_data,
        saved_preferences_response=saved_preferences_response,
    )

    # Separately persist preferences with respect to Privacy Notices where applicable.
    # Create a privacy request to propagate third party preferences if needed.
    needs_server_side_propagation: bool = False
    for privacy_preference in original_request_data.preferences:
        (
            historical_preference,
            current_preference,
        ) = PrivacyPreferenceHistory.create_history_and_upsert_current_preference(
            db=db,
            data={
                **common_user_data,
                **{
                    "preference": privacy_preference.preference,
                    "privacy_notice_history_id": privacy_preference.privacy_notice_history_id,
                    "served_notice_history_id": privacy_preference.served_notice_history_id,
                },
            },
            check_name=False,
        )
        created_historical_preferences.append(historical_preference)
        saved_preferences_response.preferences.append(
            current_preference  # type:ignore[arg-type]
        )

        if (
            historical_preference.privacy_notice_history
            and historical_preference.privacy_notice_history.enforcement_level
            == EnforcementLevel.system_wide
        ):
            # At least one privacy notice has expected system wide enforcement
            needs_server_side_propagation = True

    if needs_server_side_propagation:
        identity = (
            original_request_data.browser_identity
            if original_request_data.browser_identity
            else Identity()
        )
        if verified_provided_identity:
            # Pull the information on the ProvidedIdentity for the ConsentRequest to pass along to create a PrivacyRequest
            setattr(
                identity,
                verified_provided_identity.field_name.value,  # type:ignore[attr-defined]
                verified_provided_identity.encrypted_value[
                    "value"
                ],  # type:ignore[index]
            )

        # Privacy Request needs to be created with respect to the *historical* privacy preferences.
        # Note that we only contact third party services for consent saved for Privacy Notices at the moment.
        # TCF settings are frontend only.
        privacy_request_results: BulkPostPrivacyRequests = create_privacy_request_func(
            db=db,
            config_proxy=ConfigProxy(db),
            data=[
                PrivacyRequestCreate(
                    identity=identity,
                    policy_key=original_request_data.policy_key
                    or DEFAULT_CONSENT_POLICY,
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

    # Return a list of all the individual preferences saved

    return saved_preferences_response


def verify_previously_served_records(
    db: Session, data: PrivacyPreferencesRequest
) -> None:
    """
    Verifies that records indicating that consent was *served* are valid
    before saving a preference alongside these "served" records.
    """

    def validate_served_record(
        preference_record: Union[
            ConsentOptionCreate,
            TCFPurposeSave,
            TCFSpecialPurposeSave,
            TCFVendorSave,
            TCFFeatureSave,
            TCFSpecialFeatureSave,
        ],
        served_record_field: str,
        saved_preference_field: str,
        name_for_log: str,
    ) -> None:
        """Internal helper method to verify the ServedNoticeHistory record is a valid type for the preference
        that we're saving.

        For example, say we're saving preferences for TCF purpose with id 4, and we also have the record of serving
        TCF purpose with id 4 to the user.  This validation makes sure that the served record and the pending saved
        record are both referring to a purpose with an id of 4.
        """
        if not preference_record.served_notice_history_id:
            return

        served_notice_history: ServedNoticeHistory = get_served_notice_history(
            db, preference_record.served_notice_history_id
        )
        if getattr(served_notice_history, served_record_field, None) != getattr(
            preference_record, saved_preference_field, None
        ):
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"The ServedNoticeHistory record '{served_notice_history.id}' did not serve the {name_for_log} '{getattr(preference_record, saved_preference_field)}'.",
            )

    # Validate served record for privacy notice if applicable
    for preference in data.preferences:
        validate_served_record(
            preference_record=preference,
            served_record_field="privacy_notice_history_id",
            saved_preference_field="privacy_notice_history_id",
            name_for_log="privacy notice history",
        )

    # Validate previously record before saving it alongside privacy preferences
    # for TCF components if applicable
    for tcf_preference_type, field_name in TCF_PREFERENCES_FIELD_MAPPING.items():
        for preference in getattr(data, tcf_preference_type):
            validate_served_record(
                preference_record=preference,
                served_record_field=field_name,
                saved_preference_field="id",
                name_for_log=field_name,
            )


def update_request_with_decoded_fides_string_fields(
    request_body: PrivacyPreferencesRequest, db: Session
) -> PrivacyPreferencesRequest:
    """Update the request body with the decoded values of the TC string and AC strings if applicable"""
    if request_body.fides_string:
        tcf_contents: TCFExperienceContents = get_tcf_contents(
            db
        )  # TODO cache this so we're not building each time privacy preference is saved
        try:
            tc_str, ac_str = split_fides_string(request_body.fides_string)
            if tc_str and not CONFIG.consent.tcf_enabled:
                raise DecodeFidesStringError("TCF must be enabled to decode TC String")

            if ac_str and not CONFIG.consent.ac_enabled:
                raise DecodeFidesStringError("AC must be enabled to decode AC String")

            decoded_tc_str_request_body: FidesStringFidesPreferences = (
                decode_tc_string_to_preferences(tc_str, tcf_contents)
            )
            decoded_ac_str_request_body: FidesStringFidesPreferences = (
                decode_ac_string_to_preferences(ac_str, tcf_contents)
            )
            # We combine Vendor Consent Preferences from the TC String and AC String if applicable
            decoded_tc_str_request_body.vendor_consent_preferences = (
                decoded_tc_str_request_body.vendor_consent_preferences
                + decoded_ac_str_request_body.vendor_consent_preferences
            )
        except DecodeFidesStringError as exc:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=exc.args[0])

        # Remove the TC string from the request body now that we've decoded it
        request_body.fides_string = None
        # Add the individual sections from the TC string to the request body
        for decoded_tcf_section in decoded_tc_str_request_body.__fields__:
            setattr(
                request_body,
                decoded_tcf_section,
                getattr(decoded_tc_str_request_body, decoded_tcf_section),
            )

    return request_body


@router.patch(
    PRIVACY_PREFERENCES,
    status_code=HTTP_200_OK,
    response_model=SavePrivacyPreferencesResponse,
)
@fides_limiter.limit(CONFIG.security.public_request_rate_limit)
def save_privacy_preferences(
    *,
    db: Session = Depends(get_db),
    data: PrivacyPreferencesRequest,
    request: Request,
    response: Response,  # required for rate limiting
) -> SavePrivacyPreferencesResponse:
    """Saves privacy preferences with respect to a fides user device id.

    Creates historical records for these preferences for record keeping, and also updates current preferences.
    Creates a privacy request to propagate preferences to third party systems if applicable.
    """
    fides_string: Optional[str] = data.fides_string
    data = update_request_with_decoded_fides_string_fields(data, db)

    verify_privacy_notice_and_historical_records(
        db=db,
        notice_history_list=[
            consent_option.privacy_notice_history_id
            for consent_option in data.preferences
        ],
    )

    verify_previously_served_records(db, data)

    fides_user_provided_identity: ProvidedIdentity = (
        get_or_create_fides_user_device_id_provided_identity(
            db=db, identity_data=data.browser_identity
        )
    )

    logger.info("Saving privacy preferences with respect to fides user device id")

    try:
        saved_preferences_response: SavePrivacyPreferencesResponse = (
            save_privacy_preferences_for_identities(
                db=db,
                consent_request=None,
                verified_provided_identity=None,
                fides_user_provided_identity=fides_user_provided_identity,
                request=request,
                original_request_data=data,
            )
        )
        saved_preferences_response.fides_mobile_data = convert_fides_str_to_mobile_data(
            fides_string
        )

        return saved_preferences_response

    except (
        IdentityNotFoundException,
        PrivacyNoticeHistoryNotFound,
        SystemNotFound,
        DecodeFidesStringError,
    ) as exc:
        raise HTTPException(status_code=400, detail=exc.args[0])


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
