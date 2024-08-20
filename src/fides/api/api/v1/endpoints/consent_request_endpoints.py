from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union

from fastapi import Depends, HTTPException, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from fideslang.validation import FidesKey
from loguru import logger
from sqlalchemy import column
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session
from starlette.responses import StreamingResponse
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from fides.api.api.deps import get_config_proxy, get_db
from fides.api.api.v1.endpoints.privacy_request_endpoints import (
    create_privacy_request_func,
)
from fides.api.common_exceptions import (
    FunctionalityNotConfigured,
    IdentityVerificationException,
    MessageDispatchException,
)
from fides.api.db.seed import DEFAULT_CONSENT_POLICY
from fides.api.models.messaging import get_messaging_method
from fides.api.models.privacy_request import (
    Consent,
    ConsentRequest,
    ProvidedIdentity,
    ProvidedIdentityType,
)
from fides.api.models.property import Property
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.messaging.messaging import MessagingActionType, MessagingMethod
from fides.api.schemas.privacy_request import BulkPostPrivacyRequests
from fides.api.schemas.privacy_request import Consent as ConsentSchema
from fides.api.schemas.privacy_request import (
    ConsentPreferences,
    ConsentPreferencesWithVerificationCode,
    ConsentReport,
    ConsentRequestCreate,
    ConsentRequestResponse,
    ConsentWithExecutableStatus,
    PrivacyRequestCreate,
    VerificationCode,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.service._verification import send_verification_code_to_user
from fides.api.service.messaging.message_dispatch_service import message_send_enabled
from fides.api.util.api_router import APIRouter
from fides.api.util.consent_util import (
    get_or_create_fides_user_device_id_provided_identity,
)
from fides.api.util.endpoint_utils import validate_start_and_end_filters
from fides.api.util.logger import Pii
from fides.common.api.scope_registry import CONSENT_READ
from fides.common.api.v1.urn_registry import (
    CONSENT_REQUEST,
    CONSENT_REQUEST_PREFERENCES,
    CONSENT_REQUEST_PREFERENCES_WITH_ID,
    CONSENT_REQUEST_VERIFY,
    V1_URL_PREFIX,
)
from fides.config import CONFIG
from fides.config.config_proxy import ConfigProxy

router = APIRouter(tags=["Consent"], prefix=V1_URL_PREFIX)


CONFIG_JSON_PATH = "clients/privacy-center/config/config.json"


def _filter_consent(
    db: Session,
    query: Query,
    data_use: Optional[str] = None,
    has_gpc_flag: Optional[bool] = None,
    opt_in: Optional[bool] = None,
    created_lt: Optional[datetime] = None,
    created_gt: Optional[datetime] = None,
    updated_lt: Optional[datetime] = None,
    updated_gt: Optional[datetime] = None,
    identity: Optional[str] = None,
) -> Query:
    """Filter Consent records against the params passed in."""
    validate_start_and_end_filters(
        [
            (created_lt, created_gt, "created"),
            (updated_lt, updated_gt, "updated"),
        ]
    )

    if identity:
        hashed_identity = ProvidedIdentity.hash_value(value=identity)
        identities: Set[str] = {
            identity[0]
            for identity in ProvidedIdentity.filter(
                db=db,
                conditions=(ProvidedIdentity.hashed_value == hashed_identity),
            ).values(column("id"))
        }
        query = query.filter(Consent.provided_identity_id.in_(identities))

    if data_use:
        query = query.filter(Consent.data_use == data_use)
    if has_gpc_flag is not None:
        query = query.filter(Consent.has_gpc_flag == has_gpc_flag)
    if opt_in is not None:
        query = query.filter(Consent.opt_in == opt_in)

    if created_lt:
        query = query.filter(Consent.created_at < created_lt)
    if created_gt:
        query = query.filter(Consent.created_at > created_gt)
    if updated_lt:
        query = query.filter(Consent.updated_at < updated_lt)
    if updated_gt:
        query = query.filter(Consent.updated_at > updated_gt)
    return query


@router.get(
    CONSENT_REQUEST_PREFERENCES,
    dependencies=[Security(verify_oauth_client, scopes=[CONSENT_READ])],
    status_code=HTTP_200_OK,
    response_model=Page[ConsentReport],
)
def report_consent_requests(
    *,
    db: Session = Depends(get_db),
    params: Params = Depends(),
    data_use: Optional[str] = None,
    has_gpc_flag: Optional[bool] = None,
    opt_in: Optional[bool] = None,
    created_lt: Optional[datetime] = None,
    created_gt: Optional[datetime] = None,
    updated_lt: Optional[datetime] = None,
    updated_gt: Optional[datetime] = None,
    identity: Optional[str] = None,
) -> Union[StreamingResponse, AbstractPage[ConsentReport]]:
    """Provides a paginated list of all consent requests sorted by the most recently updated."""

    query = Consent.query(db).order_by(Consent.updated_at.desc())
    query = _filter_consent(
        db,
        query,
        data_use,
        has_gpc_flag,
        opt_in,
        created_lt,
        created_gt,
        updated_lt,
        updated_gt,
        identity,
    )
    paginated = paginate(query, params)
    paginated.items = [  # type: ignore
        _prepare_consent_report(
            db=db,
            consent=item,
        )
        for item in paginated.items  # type: ignore
    ]
    return paginated


@router.post(
    CONSENT_REQUEST,
    status_code=HTTP_200_OK,
    response_model=ConsentRequestResponse,
)
def create_consent_request(
    *,
    db: Session = Depends(get_db),
    config_proxy: ConfigProxy = Depends(get_config_proxy),
    data: ConsentRequestCreate,
) -> ConsentRequestResponse:
    """Creates a verification code for the user to verify access to manage consent preferences."""
    if not CONFIG.redis.enabled:
        raise FunctionalityNotConfigured(
            "Application redis cache required, but it is currently disabled! Please update your application configuration to enable integration with a redis cache."
        )
    # TODO: (PROD-2142)- pass in property id here
    if data.property_id:
        valid_property: Optional[Property] = Property.get_by(
            db, field="id", value=data.property_id
        )
        if not valid_property:
            raise HTTPException(
                HTTP_400_BAD_REQUEST,
                detail="The property id provided is invalid",
            )

    identity = data.identity
    if (
        not identity.email
        and not identity.phone_number
        and not identity.fides_user_device_id
        and not identity.external_id
    ):
        raise HTTPException(
            HTTP_400_BAD_REQUEST,
            detail="An email address, phone number, fides_user_device_id, or external_id is required",
        )

    provided_identity = _get_or_create_provided_identity(
        db=db,
        identity_data=identity,
    )

    consent_request_data = {
        "provided_identity_id": provided_identity.id,
        "property_id": getattr(data, "property_id", None),
        "source": getattr(data, "source", None),
    }
    consent_request = ConsentRequest.create(db, data=consent_request_data)

    consent_request.persist_custom_privacy_request_fields(
        db=db, custom_privacy_request_fields=data.custom_privacy_request_fields
    )
    if message_send_enabled(
        db,
        data.property_id,
        MessagingActionType.SUBJECT_IDENTITY_VERIFICATION,
        not config_proxy.execution.disable_consent_identity_verification,
    ):
        try:
            send_verification_code_to_user(
                db, consent_request, data.identity, data.property_id
            )
        except MessageDispatchException as exc:
            logger.error("Error sending the verification code message: {}", str(exc))
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error sending the verification code message: {str(exc)}",
            )

    return ConsentRequestResponse(
        identity=identity,
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
    """Verifies the verification code and returns the current consent preferences if successful.

    Note that this returns just Consent records - which is the old workflow that saves Consent with respect to a data use.
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

    return _prepare_consent_preferences(db, provided_identity)


@router.get(
    CONSENT_REQUEST_PREFERENCES_WITH_ID,
    status_code=HTTP_200_OK,
    response_model=ConsentPreferences,
    responses={
        HTTP_200_OK: {
            "consent": [
                {
                    "data_use": "marketing.advertising",
                    "data_use_description": "We may use some of your personal information for advertising performance "
                    "analysis and audience modeling for ongoing advertising which may be "
                    "interpreted as 'Data Sharing' under some regulations.",
                    "opt_in": True,
                    "highlight": False,
                },
                {
                    "data_use": "functional",
                    "data_use_description": "We may use some of your personal information to collect analytics about "
                    "how you use our products & services, in order to improve our service.",
                    "opt_in": False,
                },
            ]
        },
        HTTP_404_NOT_FOUND: {"detail": "Consent request not found"},
        HTTP_400_BAD_REQUEST: {
            "detail": "Retrieving consent preferences without identity verification is "
            "only supported with disable_consent_identity_verification set to true"
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

    if not config_proxy.execution.disable_consent_identity_verification:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Retrieving consent preferences without identity verification is "
            "only supported with disable_consent_identity_verification set to true",
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


def queue_privacy_request_to_propagate_consent_old_workflow(
    db: Session,
    provided_identity: ProvidedIdentity,
    policy: Union[FidesKey, str],
    consent_preferences: ConsentPreferences,
    consent_request: ConsentRequest,
    executable_consents: Optional[List[ConsentWithExecutableStatus]] = [],
    browser_identity: Optional[Identity] = None,
) -> Optional[BulkPostPrivacyRequests]:
    """
    Queue a privacy request to carry out propagating consent preferences server-side to third-party systems.

    Only propagate consent preferences which are considered "executable" by the current system. If none of the
    consent preferences are executable, no Privacy Request is queued.

    # TODO Slated for deprecation
    """
    # Create an identity based on any provided browser_identity
    identity = browser_identity if browser_identity else Identity()
    setattr(
        identity,
        provided_identity.field_name,  # type:ignore[attr-defined]
        provided_identity.encrypted_value["value"],  # type:ignore[index]
    )  # Pull the information on the ProvidedIdentity for the ConsentRequest to pass along to create a PrivacyRequest

    executable_data_uses = [
        ec.data_use for ec in executable_consents or [] if ec.executable
    ]

    # Restrict consent preferences to just those that are executable
    executable_consent_preferences: List[Dict] = [
        pref.model_dump(mode="json")
        for pref in consent_preferences.consent or []
        if pref.data_use in executable_data_uses
    ]

    if not executable_consent_preferences:
        logger.info(
            "Skipping propagating consent preferences to third-party services as "
            "specified consent preferences: {} are not executable.",
            [pref.data_use for pref in consent_preferences.consent or []],
        )
        return None

    logger.info("Executable consent options: {}", executable_data_uses)
    privacy_request_results: BulkPostPrivacyRequests = create_privacy_request_func(
        db=db,
        config_proxy=ConfigProxy(db),
        data=[
            PrivacyRequestCreate(
                identity=identity,
                policy_key=policy,
                consent_preferences=executable_consent_preferences,
                consent_request_id=consent_request.id,
                custom_privacy_request_fields=consent_request.get_persisted_custom_privacy_request_fields(),
                source=consent_request.source,
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

    Note that this allows you to save Consent records under our old workflow that saves Consent with respect to a data use.

    # TODO Slated for deprecation
    """
    consent_request, provided_identity = _get_consent_request_and_provided_identity(
        db=db,
        consent_request_id=consent_request_id,
        verification_code=data.code,
    )
    consent_request.preferences = [
        schema.model_dump(mode="json") for schema in data.consent
    ]
    consent_request.save(db=db)

    if not provided_identity.hashed_value:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Provided identity missing"
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

    consent_preferences: ConsentPreferences = _prepare_consent_preferences(
        db, provided_identity
    )

    # Note: This just queues the PrivacyRequest for processing
    privacy_request_creation_results: Optional[BulkPostPrivacyRequests] = (
        queue_privacy_request_to_propagate_consent_old_workflow(
            db,
            provided_identity,
            data.policy_key or DEFAULT_CONSENT_POLICY,
            consent_preferences,
            consent_request,
            data.executable_options,
            data.browser_identity,
        )
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
                (ProvidedIdentity.field_name == ProvidedIdentityType.email.value)
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
                (ProvidedIdentity.field_name == ProvidedIdentityType.phone_number.value)
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
    elif target_identity_type == ProvidedIdentityType.fides_user_device_id.value:
        identity = get_or_create_fides_user_device_id_provided_identity(
            db, identity_data
        )
    elif (
        target_identity_type == ProvidedIdentityType.external_id.value
        and identity_data.external_id
    ):
        identity = ProvidedIdentity.filter(
            db=db,
            conditions=(
                (ProvidedIdentity.field_name == ProvidedIdentityType.external_id.value)
                & (
                    ProvidedIdentity.hashed_value
                    == ProvidedIdentity.hash_value(identity_data.external_id)
                )
                & (ProvidedIdentity.privacy_request_id.is_(None))
            ),
        ).first()
        if not identity:
            identity = ProvidedIdentity.create(
                db,
                data={
                    "privacy_request_id": None,
                    "field_name": ProvidedIdentityType.external_id.value,
                    "hashed_value": ProvidedIdentity.hash_value(
                        identity_data.external_id
                    ),
                    "encrypted_value": {"value": identity_data.external_id},
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
    Consent requests, unlike privacy requests, only accept 1 identity type: email,
    phone, external_id, or fides_user_device_id. These identity types are configurable
    as optional/required within the privacy center config.json. If both email and phone
    identity types are provided, we'll use the identity type defined in
    CONFIG.notifications.notification_service_type. Otherwise, the fallback order is
    email, phone_number, external_id, and finally fides_user_device_id.
    """
    target_identity_type = ""

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
    elif identity_data.external_id:
        target_identity_type = ProvidedIdentityType.external_id.value
    elif identity_data.fides_user_device_id:
        # If no other identity is provided, use the Fides User Device ID
        target_identity_type = ProvidedIdentityType.fides_user_device_id.value

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

    if not ConfigProxy(db).execution.disable_consent_identity_verification:
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


def _prepare_consent_report(
    db: Session,
    consent: Consent,
) -> ConsentReport:
    """Enhances a consent request with identity, created and updated timestamps."""
    provided_identity = ProvidedIdentity.get_by(
        db=db,
        field="id",
        value=consent.provided_identity_id,
    )
    consent.identity = provided_identity.as_identity_schema()  # type: ignore[union-attr]
    report = ConsentReport.model_validate(consent)
    return report


def _prepare_consent_preferences(
    db: Session,
    provided_identity: ProvidedIdentity,
) -> ConsentPreferences:
    """Returns consent preferences for the identity given."""
    consent_records: List[Consent] = (
        Consent.filter(
            db=db, conditions=Consent.provided_identity_id == provided_identity.id
        )
        .order_by(Consent.updated_at)
        .all()
    )

    if not consent_records:
        return ConsentPreferences(consent=None)

    return ConsentPreferences(
        consent=[
            ConsentSchema(
                data_use=x.data_use,
                data_use_description=x.data_use_description,
                opt_in=x.opt_in,
                has_gpc_flag=x.has_gpc_flag,
                conflicts_with_gpc=x.conflicts_with_gpc,
            )
            for x in consent_records
        ],
    )
