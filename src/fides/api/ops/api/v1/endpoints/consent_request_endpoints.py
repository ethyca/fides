from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union

from fastapi import Depends, HTTPException, Security
from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from fides.api.ctl.database.seed import DEFAULT_CONSENT_POLICY
from fides.api.ops.api.deps import get_config_proxy, get_db
from fides.api.ops.api.v1.endpoints.privacy_request_endpoints import (
    create_privacy_request_func,
)
from fides.api.ops.api.v1.scope_registry import CONSENT_READ
from fides.api.ops.api.v1.urn_registry import (
    CONSENT_REQUEST,
    CONSENT_REQUEST_PREFERENCES,
    CONSENT_REQUEST_PREFERENCES_WITH_ID,
    CONSENT_REQUEST_VERIFY,
    V1_URL_PREFIX,
)
from fides.api.ops.common_exceptions import (
    FunctionalityNotConfigured,
    IdentityVerificationException,
    MessageDispatchException,
)
from fides.api.ops.models.messaging import get_messaging_method
from fides.api.ops.models.privacy_notice import PrivacyNoticeHistory
from fides.api.ops.models.privacy_request import (
    Consent,
    ConsentRequest,
    ProvidedIdentity,
    ProvidedIdentityType,
)
from fides.api.ops.schemas.messaging.messaging import MessagingMethod
from fides.api.ops.schemas.privacy_request import (
    Consent as ConsentSchema,
    BulkPostPrivacyRequests,
    ConsentPreferences,
    ConsentPreferencesWithVerificationCode,
    ConsentRequestResponse,
    ConsentWithExecutableStatus,
    PrivacyRequestCreate,
    VerificationCode,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service._verification import send_verification_code_to_user
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.logger import Pii
from fides.api.ops.util.oauth_util import verify_oauth_client
from fides.core.config import CONFIG
from fides.core.config.config_proxy import ConfigProxy

router = APIRouter(tags=["Consent"], prefix=V1_URL_PREFIX)


CONFIG_JSON_PATH = "clients/privacy-center/config/config.json"


@router.post(
    CONSENT_REQUEST,
    status_code=HTTP_200_OK,
    response_model=ConsentRequestResponse,
)
def create_consent_request(
    *,
    db: Session = Depends(get_db),
    config_proxy: ConfigProxy = Depends(get_config_proxy),
    data: Identity,
) -> ConsentRequestResponse:
    """Creates a verification code for the user to verify access to manage consent preferences."""
    if not CONFIG.redis.enabled:
        raise FunctionalityNotConfigured(
            "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a redis cache."
        )

    if not data.email and not data.phone_number:
        raise HTTPException(
            HTTP_400_BAD_REQUEST,
            detail="An email address or phone number identity is required",
        )

    identity = _get_or_create_provided_identity(
        db=db,
        identity_data=data,
    )

    consent_request_data = {
        "provided_identity_id": identity.id,
    }
    consent_request = ConsentRequest.create(db, data=consent_request_data)

    if config_proxy.execution.subject_identity_verification_required:
        try:
            send_verification_code_to_user(db, consent_request, data)
        except MessageDispatchException as exc:
            logger.error("Error sending the verification code message: {}", str(exc))
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error sending the verification code message: {str(exc)}",
            )
    return ConsentRequestResponse(
        identity=data,
        consent_request_id=consent_request.id,
    )


@router.post(
    CONSENT_REQUEST_VERIFY,
    status_code=HTTP_200_OK,
    response_model=ConsentPreferences,
)
def consent_request_verify(
    *,
    consent_request_id: str,
    db: Session = Depends(get_db),
    data: VerificationCode,
) -> ConsentPreferences:
    """Verifies the verification code and returns the current consent preferences if successful."""
    _, provided_identity = _get_consent_request_and_provided_identity(
        db=db,
        consent_request_id=consent_request_id,
        verification_code=data.code,
    )

    if not provided_identity.hashed_value:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Provided identity missing"
        )

    return _prepare_consent_preferences(db, provided_identity)


@router.get(
    CONSENT_REQUEST_PREFERENCES_WITH_ID,
    status_code=HTTP_200_OK,
    response_model=ConsentPreferences,
    responses={
        HTTP_200_OK: {
            "consent": [
                {
                    "data_use": "advertising",
                    "data_use_description": "We may use some of your personal information for advertising performance "
                    "analysis and audience modeling for ongoing advertising which may be "
                    "interpreted as 'Data Sharing' under some regulations.",
                    "opt_in": True,
                    "highlight": False,
                },
                {
                    "data_use": "improve",
                    "data_use_description": "We may use some of your personal information to collect analytics about "
                    "how you use our products & services, in order to improve our service.",
                    "opt_in": False,
                },
            ]
        },
        HTTP_404_NOT_FOUND: {"detail": "Consent request not found"},
        HTTP_400_BAD_REQUEST: {
            "detail": "Retrieving consent preferences without identity verification is "
            "only supported with subject_identity_verification_required "
            "turned off."
        },
    },
)
def get_consent_preferences_no_id(
    *,
    db: Session = Depends(get_db),
    config_proxy: ConfigProxy = Depends(get_config_proxy),
    consent_request_id: str,
) -> ConsentPreferences:
    """Returns the current consent preferences if successful."""

    if config_proxy.execution.subject_identity_verification_required:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Retrieving consent preferences without identity verification is "
            "only supported with subject_identity_verification_required "
            "turned off.",
        )

    _, provided_identity = _get_consent_request_and_provided_identity(
        db=db,
        consent_request_id=consent_request_id,
        verification_code=None,
    )

    if not provided_identity.hashed_value:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Provided identity missing"
        )

    return _prepare_consent_preferences(db, provided_identity)


@router.post(
    CONSENT_REQUEST_PREFERENCES,
    dependencies=[Security(verify_oauth_client, scopes=[CONSENT_READ])],
    status_code=HTTP_200_OK,
    response_model=ConsentPreferences,
)
def get_consent_preferences(
    *,
    db: Session = Depends(get_db),
    data: Identity,
) -> ConsentPreferences:
    """Gets the consent preferences for the specified user."""
    if not data.email and not data.phone_number:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="No identity information provided"
        )

    # From the above check we know at least one exists
    lookup = data.email if data.email else data.phone_number

    identity = ProvidedIdentity.filter(
        db,
        conditions=(
            (ProvidedIdentity.hashed_value == ProvidedIdentity.hash_value(str(lookup)))
            & (ProvidedIdentity.privacy_request_id.is_(None))
        ),
    ).first()

    if not identity:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Identity not found")

    return _prepare_consent_preferences(db, identity)


def queue_privacy_request_to_propagate_consent(
    db: Session,
    provided_identity: ProvidedIdentity,
    policy: Union[FidesKey, str],
    consent_preferences: ConsentPreferences,
    executable_consents: Optional[List[ConsentWithExecutableStatus]] = [],
    browser_identity: Optional[Identity] = None,
) -> Optional[BulkPostPrivacyRequests]:
    """
    Queue a privacy request to carry out propagating consent preferences server-side to third-party systems.

    For the old workflow, only propagate consent preferences which are considered "executable" by the current system.
    For the new workflow, propagate all consent preferences.
    Privacy requests are queued regardless of whether there are consent preferences to propagate.
    """
    # Create an identity based on any provided browser_identity
    identity = browser_identity if browser_identity else Identity()
    setattr(
        identity,
        provided_identity.field_name.value,  # type:ignore[attr-defined]
        provided_identity.encrypted_value["value"],  # type:ignore[index]
    )  # Pull the information on the ProvidedIdentity for the ConsentRequest to pass along to create a PrivacyRequest

    executable_data_uses = [
        ec.data_use for ec in executable_consents or [] if ec.executable
    ]

    executable_consent_preferences: List[Dict] = []
    for pref in consent_preferences.consent or []:
        if (
            pref.data_use and pref.data_use in executable_data_uses
        ) or pref.privacy_notice_id:
            executable_consent_preferences.append(pref.dict())

    privacy_request_results: BulkPostPrivacyRequests = create_privacy_request_func(
        db=db,
        config_proxy=ConfigProxy(db),
        data=[
            PrivacyRequestCreate(
                identity=identity,
                policy_key=policy,
                consent_preferences=executable_consent_preferences,
            )
        ],
        authenticated=True,
    )

    if privacy_request_results.failed or not privacy_request_results.succeeded:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=privacy_request_results.failed[0].message,
        )

    return privacy_request_results


def _save_consent_preferences(
    provided_identity: ProvidedIdentity,
    db: Session,
    consent_preference_data: List[ConsentSchema],
) -> List[Consent]:
    """Upsert Consent Preferences

    For the old workflow: Updated existing Consent record with same data_use and provided identity. Otherwise, create a new one.
    For the new workflow: Update an Existing Consent Record associated with the same Privacy Notice History record and provided identity.
    Otherwise create a new one.

    """
    upserted_consent_preferences: List[Consent] = []

    if any(pref.data_use for pref in consent_preference_data) and any(
        pref.privacy_notice_id for pref in consent_preference_data
    ):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Request has consent preferences saved for both data uses and privacy notices.  Migrate to using privacy notices.",
        )

    for preference in consent_preference_data:
        current_preference: Optional[Consent] = None
        privacy_notice_history: Optional[PrivacyNoticeHistory] = None

        # Old workflow; slated to be deleted
        if preference.data_use:
            current_preference = Consent.filter(
                db=db,
                conditions=(Consent.provided_identity_id == provided_identity.id)
                & (Consent.data_use == preference.data_use),
            ).first()
        # New workflow; preferences saved with respect to privacy notices
        elif preference.privacy_notice_id and preference.privacy_notice_version:
            # New workflow
            privacy_notice_history = PrivacyNoticeHistory.get_by_notice_and_version(
                db, preference.privacy_notice_id, preference.privacy_notice_version
            )
            if not privacy_notice_history:
                raise HTTPException(
                    HTTP_404_NOT_FOUND,
                    detail=f"No PrivacyNoticeHistory record for '{preference.privacy_notice_id}' "
                    f"version '{preference.privacy_notice_version}'",
                )
            current_preference = Consent.get_consent_for_identity_and_history(
                db, provided_identity.id, privacy_notice_history.id
            )

        preference_dict = preference.dict()
        preference_dict["privacy_notice_history_id"] = (
            privacy_notice_history.id if privacy_notice_history else None
        )

        if current_preference:
            current_preference.update(db, data=preference_dict)
        else:
            preference_dict["provided_identity_id"] = provided_identity.id
            try:
                current_preference = Consent.create(db, data=preference_dict)
            except IntegrityError as exc:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST, detail=Pii(str(exc))
                )
        upserted_consent_preferences.append(current_preference)  # type: ignore[arg-type]

    return upserted_consent_preferences


@router.patch(
    CONSENT_REQUEST_PREFERENCES_WITH_ID,
    status_code=HTTP_200_OK,
    response_model=ConsentPreferences,
)
def set_consent_preferences(
    *,
    consent_request_id: str,
    db: Session = Depends(get_db),
    data: ConsentPreferencesWithVerificationCode,
) -> ConsentPreferences:
    """Verifies the verification code and saves the user's consent preferences if successful.

    Two workflows are accommodated here:
    1) Old workflow, where consent preferences are saved with regards to data uses
    2) New workflow where consent preferences are saved with regards to privacy notices
    """
    consent_request, provided_identity = _get_consent_request_and_provided_identity(
        db=db,
        consent_request_id=consent_request_id,
        verification_code=data.code,
    )
    if not provided_identity.hashed_value:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Provided identity missing"
        )

    upserted_consent_preferences: List[Consent] = _save_consent_preferences(
        provided_identity, db, data.consent
    )

    # Don't re-retrieve all consent preferences from the database: just the preferences
    # asserted with this request.
    consent_preferences: ConsentPreferences = ConsentPreferences(
        consent=upserted_consent_preferences
    )

    # Save consent preferences on the Consent Request too
    consent_request.preferences = [
        schema.dict() for schema in consent_preferences.consent or []
    ]
    consent_request.save(db=db)

    # Queue a privacy request for propagating preferences
    privacy_request_creation_results: Optional[
        BulkPostPrivacyRequests
    ] = queue_privacy_request_to_propagate_consent(
        db,
        provided_identity,
        data.policy_key or DEFAULT_CONSENT_POLICY,
        consent_preferences,
        data.executable_options,
        data.browser_identity,
    )

    if privacy_request_creation_results:
        consent_request.privacy_request_id = privacy_request_creation_results.succeeded[
            0
        ].id
        consent_request.save(db=db)

    return consent_preferences


def _get_or_create_provided_identity(
    db: Session,
    identity_data: Identity,
) -> ProvidedIdentity:
    """Based on target identity type, retrieves or creates associated ProvidedIdentity"""
    target_identity_type: str = infer_target_identity_type(db, identity_data)

    if target_identity_type == ProvidedIdentityType.email.value and identity_data.email:
        identity = ProvidedIdentity.filter(
            db=db,
            conditions=(
                (ProvidedIdentity.field_name == ProvidedIdentityType.email)
                & (
                    ProvidedIdentity.hashed_value
                    == ProvidedIdentity.hash_value(identity_data.email)
                )
                & (ProvidedIdentity.privacy_request_id.is_(None))
            ),
        ).first()
        if not identity:
            identity = ProvidedIdentity.create(
                db,
                data={
                    "privacy_request_id": None,
                    "field_name": ProvidedIdentityType.email.value,
                    "hashed_value": ProvidedIdentity.hash_value(identity_data.email),
                    "encrypted_value": {"value": identity_data.email},
                },
            )
    elif (
        target_identity_type == ProvidedIdentityType.phone_number.value
        and identity_data.phone_number
    ):
        identity = ProvidedIdentity.filter(
            db=db,
            conditions=(
                (ProvidedIdentity.field_name == ProvidedIdentityType.phone_number)
                & (
                    ProvidedIdentity.hashed_value
                    == ProvidedIdentity.hash_value(identity_data.phone_number)
                )
                & (ProvidedIdentity.privacy_request_id.is_(None))
            ),
        ).first()
        if not identity:
            identity = ProvidedIdentity.create(
                db,
                data={
                    "privacy_request_id": None,
                    "field_name": ProvidedIdentityType.phone_number.value,
                    "hashed_value": ProvidedIdentity.hash_value(
                        identity_data.phone_number
                    ),
                    "encrypted_value": {"value": identity_data.phone_number},
                },
            )
    else:
        raise HTTPException(
            HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Identity type not found in identity data",
        )
    return identity


def infer_target_identity_type(
    db: Session,
    identity_data: Identity,
) -> str:
    """
    Consent requests, unlike privacy requests, only accept 1 identity type- email or phone.
    These identity types are configurable as optional/required within the privacy center config.json.
    If both identity types are provided, we'll use identity type if defined in
    CONFIG.notifications.notification_service_type, else default to email.
    """
    if identity_data.email and identity_data.phone_number:
        messaging_method = get_messaging_method(
            ConfigProxy(db).notifications.notification_service_type
        )
        if messaging_method == MessagingMethod.EMAIL:
            target_identity_type = ProvidedIdentityType.email.value
        elif messaging_method == MessagingMethod.SMS:
            target_identity_type = ProvidedIdentityType.phone_number.value
        else:
            target_identity_type = ProvidedIdentityType.email.value
    elif identity_data.email:
        target_identity_type = ProvidedIdentityType.email.value
    elif identity_data.phone_number:
        target_identity_type = ProvidedIdentityType.phone_number.value
    return target_identity_type


def _get_consent_request_and_provided_identity(
    db: Session,
    consent_request_id: str,
    verification_code: Optional[str],
) -> Tuple[ConsentRequest, ProvidedIdentity]:
    """Verifies the consent request and verification code, then return the ProvidedIdentity if successful."""
    consent_request = ConsentRequest.get_by_key_or_id(
        db=db, data={"id": consent_request_id}
    )

    if not consent_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Consent request not found",
        )

    if ConfigProxy(db).execution.subject_identity_verification_required:
        try:
            consent_request.verify_identity(
                db,
                verification_code,
            )
        except IdentityVerificationException as exc:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=exc.message)
        except PermissionError as exc:
            logger.info(
                "Invalid verification code provided for {}.", consent_request.id
            )
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=exc.args[0])

    provided_identity: ProvidedIdentity | None = ProvidedIdentity.get_by_key_or_id(
        db,
        data={"id": consent_request.provided_identity_id},
    )

    # It shouldn't be possible to hit this because the cascade delete of the identity
    # data would also delete the consent_request, but including this as a safety net.
    if not provided_identity:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No identity found for consent request id",
        )

    return consent_request, provided_identity


def _prepare_consent_preferences(
    db: Session, provided_identity: ProvidedIdentity
) -> ConsentPreferences:
    """Query existing consent preferences for the current provided identity

    Return all preferences associated with old "data_uses", as well as the preferences
    saved for the latest version of privacy notices.
    """
    consent_preferences: List[Consent] = Consent.get_current_consent_preferences(
        db, provided_identity
    )
    return ConsentPreferences(consent=consent_preferences or None)
