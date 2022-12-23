from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Security
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from fides.api.ops.api.deps import get_db
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
from fides.api.ops.models.privacy_request import (
    Consent,
    ConsentRequest,
    ProvidedIdentity,
    ProvidedIdentityType,
)
from fides.api.ops.schemas.privacy_request import Consent as ConsentSchema
from fides.api.ops.schemas.privacy_request import (
    ConsentPreferences,
    ConsentPreferencesWithVerificationCode,
    ConsentRequestResponse,
    VerificationCode,
)
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service._verification import send_verification_code_to_user
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.logger import Pii
from fides.api.ops.util.oauth_util import verify_oauth_client
from fides.core.config import get_config

router = APIRouter(tags=["Consent"], prefix=V1_URL_PREFIX)

CONFIG = get_config()


@router.post(
    CONSENT_REQUEST,
    status_code=HTTP_200_OK,
    response_model=ConsentRequestResponse,
)
def create_consent_request(
    *,
    db: Session = Depends(get_db),
    data: Identity,
) -> ConsentRequestResponse:
    """Creates a verification code for the user to verify access to manage consent preferences."""
    if not CONFIG.redis.enabled:
        raise FunctionalityNotConfigured(
            "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a redis cache."
        )

    if not data.email:
        raise HTTPException(HTTP_400_BAD_REQUEST, detail="An email address is required")

    identity = ProvidedIdentity.filter(
        db=db,
        conditions=(
            (ProvidedIdentity.field_name == ProvidedIdentityType.email)
            & (ProvidedIdentity.hashed_value == ProvidedIdentity.hash_value(data.email))
            & (ProvidedIdentity.privacy_request_id.is_(None))
        ),
    ).first()

    if not identity:
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "hashed_value": ProvidedIdentity.hash_value(data.email),
            "encrypted_value": {"value": data.email},
        }
        identity = ProvidedIdentity.create(db, data=provided_identity_data)

    consent_request_data = {
        "provided_identity_id": identity.id,
    }
    consent_request = ConsentRequest.create(db, data=consent_request_data)

    if CONFIG.execution.subject_identity_verification_required:
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
    provided_identity = _get_consent_request_and_provided_identity(
        db=db, consent_request_id=consent_request_id, verification_code=data.code
    )

    if not provided_identity.hashed_value:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Provided identity missing email"
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
    *, db: Session = Depends(get_db), consent_request_id: str
) -> ConsentPreferences:
    """Returns the current consent preferences if successful."""

    if CONFIG.execution.subject_identity_verification_required:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Retrieving consent preferences without identity verification is "
            "only supported with subject_identity_verification_required "
            "turned off.",
        )

    provided_identity = _get_consent_request_and_provided_identity(
        db=db, consent_request_id=consent_request_id, verification_code=None
    )

    if not provided_identity.hashed_value:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Provided identity missing email"
        )

    return _prepare_consent_preferences(db, provided_identity)


@router.post(
    CONSENT_REQUEST_PREFERENCES,
    dependencies=[Security(verify_oauth_client, scopes=[CONSENT_READ])],
    status_code=HTTP_200_OK,
    response_model=ConsentPreferences,
)
def get_consent_preferences(
    *, db: Session = Depends(get_db), data: Identity
) -> ConsentPreferences:
    """Gets the consent preferences for the specified user."""
    if data.email:
        lookup = data.email
    elif data.phone_number:
        lookup = data.phone_number
    else:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="No identity information provided"
        )

    identity = ProvidedIdentity.filter(
        db,
        conditions=(
            (ProvidedIdentity.hashed_value == ProvidedIdentity.hash_value(lookup))
            & (ProvidedIdentity.privacy_request_id.is_(None))
        ),
    ).first()

    if not identity:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Identity not found")

    return _prepare_consent_preferences(db, identity)


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
    """Verifies the verification code and saves the user's consent preferences if successful."""
    provided_identity = _get_consent_request_and_provided_identity(
        db=db,
        consent_request_id=consent_request_id,
        verification_code=data.code,
    )

    if not provided_identity.hashed_value:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Provided identity missing email"
        )

    for preference in data.consent:
        current_preference = Consent.filter(
            db=db,
            conditions=(Consent.provided_identity_id == provided_identity.id)
            & (Consent.data_use == preference.data_use),
        ).first()

        if current_preference:
            current_preference.update(db, data=dict(preference))
        else:
            preference_dict = dict(preference)
            preference_dict["provided_identity_id"] = provided_identity.id
            try:
                Consent.create(db, data=preference_dict)
            except IntegrityError as exc:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST, detail=Pii(str(exc))
                )

    return _prepare_consent_preferences(db, provided_identity)


def _get_consent_request_and_provided_identity(
    db: Session,
    consent_request_id: str,
    verification_code: Optional[str],
) -> ProvidedIdentity:
    """Verifies the consent request and verification code, then return the ProvidedIdentity if successful."""
    consent_request = ConsentRequest.get_by_key_or_id(
        db=db, data={"id": consent_request_id}
    )

    if not consent_request:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Consent request not found"
        )

    if CONFIG.execution.subject_identity_verification_required:
        try:
            consent_request.verify_identity(verification_code)
        except IdentityVerificationException as exc:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=exc.message)
        except PermissionError as exc:
            logger.info(
                "Invalid verification code provided for {}.", consent_request.id
            )
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail=exc.args[0])

    provided_identity: ProvidedIdentity | None = ProvidedIdentity.get_by_key_or_id(
        db, data={"id": consent_request.provided_identity_id}
    )

    # It shouldn't be possible to hit this because the cascade delete of the identity
    # data would also delete the consent_request, but including this as a safety net.
    if not provided_identity:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No identity found for consent request id",
        )

    return provided_identity


def _prepare_consent_preferences(
    db: Session, provided_identity: ProvidedIdentity
) -> ConsentPreferences:
    consent = Consent.filter(
        db=db, conditions=Consent.provided_identity_id == provided_identity.id
    ).all()

    if not consent:
        return ConsentPreferences(consent=None)

    return ConsentPreferences(
        consent=[
            ConsentSchema(
                data_use=x.data_use,
                data_use_description=x.data_use_description,
                opt_in=x.opt_in,
            )
            for x in consent
        ],
    )
