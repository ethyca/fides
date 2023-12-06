from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import BackgroundTasks, Depends, HTTPException, Request, Response
from loguru import logger
from sqlalchemy.orm import Query, Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api.deps import get_db
from fides.api.api.v1.endpoints.consent_request_endpoints import (
    _get_consent_request_and_provided_identity,
)
from fides.api.api.v1.endpoints.privacy_preference_endpoints import (
    anonymize_ip_address,
    get_ip_address,
    verify_privacy_notice_and_historical_records,
)
from fides.api.common_exceptions import (
    IdentityNotFoundException,
    PrivacyNoticeHistoryNotFound,
)
from fides.api.custom_types import SafeStr
from fides.api.db.ctl_session import sync_session
from fides.api.models.privacy_experience import PrivacyExperience
from fides.api.models.privacy_notice import PrivacyNoticeHistory
from fides.api.models.privacy_preference_v2 import (
    ConsentIdentitiesMixin,
    LastServedNoticeV2,
    ServedNoticeHistoryV2,
    get_records_with_consent_identifiers,
)
from fides.api.models.privacy_request import ProvidedIdentity, ProvidedIdentityType
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_preference import RecordConsentServedRequest
from fides.api.schemas.privacy_preference_v2 import RecordsServed, RecordsServedResponse
from fides.api.schemas.redis_cache import Identity
from fides.api.util.api_router import APIRouter
from fides.api.util.endpoint_utils import fides_limiter
from fides.common.api.v1.urn_registry import (
    CONSENT_REQUEST_NOTICES_SERVED,
    NOTICES_SERVED,
    V1_URL_PREFIX,
)
from fides.config import CONFIG

router = APIRouter(tags=["Privacy Preference"], prefix=V1_URL_PREFIX)


def get_privacy_experience_or_error(
    db: Session, privacy_experience_id: Optional[str]
) -> Optional[PrivacyExperience]:
    """Check if privacy_experience_id is valid if supplied"""
    if not privacy_experience_id:
        return None

    privacy_experience = PrivacyExperience.get(db=db, object_id=privacy_experience_id)
    if not privacy_experience:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Privacy Experience '{privacy_experience_id}' not found.",
        )

    return privacy_experience


def get_identifiers_from_privacy_center_request(
    provided_identity: ProvidedIdentity, browser_identity: Identity
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract user identifiers from privacy center request - either through verified provided identities or the
    fides user device id"""
    email: Optional[str] = None
    phone_number: Optional[str] = None
    fides_user_device: Optional[str] = None

    # Get identifier value off of ProvidedIdentity value created for identity verification.
    # It is also possible Privacy Center didn't collect an email or phone number for customers
    # just wanted to record against device id
    if provided_identity.encrypted_value:
        identifier = provided_identity.encrypted_value.get("value")
        if provided_identity.field_name == ProvidedIdentityType.email:
            email = identifier
        if provided_identity.field_name == ProvidedIdentityType.phone_number:
            phone_number = identifier
        if provided_identity.field_name == ProvidedIdentityType.fides_user_device_id:
            fides_user_device = identifier

    if not (email or phone_number or fides_user_device):
        # Currently a valid provided identity with an identifier is required if request comes th
        raise IdentityNotFoundException("User identities not found")

    # If no fides user device id from provided identity, pull off of request
    if not fides_user_device:
        fides_user_device = get_fides_user_device_id_from_request(
            browser_identity, throw_exception=False
        )

    return email, phone_number, fides_user_device


@router.patch(
    CONSENT_REQUEST_NOTICES_SERVED,
    status_code=HTTP_200_OK,
    response_model=RecordsServedResponse,
)
def save_consent_served_via_privacy_center_v2(
    *,
    consent_request_id: str,
    db: Session = Depends(get_db),
    data: RecordConsentServedRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> Dict:
    """Saves that consent was served via a verified identity flow (privacy center) v2

    Capable of saving that consent was served against a verified email/phone number and a fides user device id
    simultaneously.
    """
    verify_privacy_notice_and_historical_records(
        db=db,
        notice_history_list=data.privacy_notice_history_ids,
    )

    get_privacy_experience_or_error(db, data.privacy_experience_id)

    _, provided_identity = _get_consent_request_and_provided_identity(
        db=db,
        consent_request_id=consent_request_id,
        verification_code=data.code,
    )

    logger.info("Saving notices served for privacy center")

    try:
        (
            email,
            phone_number,
            fides_user_device,
        ) = get_identifiers_from_privacy_center_request(
            provided_identity, data.browser_identity
        )

        last_served_record, task_data = save_last_served_and_prep_task_data(
            db=db,
            request=request,
            request_data=data,
            fides_user_device=fides_user_device,
            email=email,
            phone_number=phone_number,
        )

        served: Dict = last_served_record.served or {}
        # Overriding privacy notice history ids on response so previously saved
        # data isn't returned
        served["privacy_notice_history_ids"] = data.privacy_notice_history_ids
        served["served_notice_history_id"] = task_data["served_notice_history_id"]

        background_tasks.add_task(save_consent_served_task, task_data)
        return served
    except (
        IdentityNotFoundException,
        PrivacyNoticeHistoryNotFound,
    ) as exc:
        raise HTTPException(status_code=400, detail=exc.args[0])


@router.patch(
    NOTICES_SERVED,
    status_code=HTTP_200_OK,
    response_model=RecordsServedResponse,
)
@fides_limiter.limit(CONFIG.security.public_request_rate_limit)
def save_consent_served_to_user_v2(
    *,
    db: Session = Depends(get_db),
    data: RecordConsentServedRequest,
    request: Request,
    response: Response,  # required for rate limiting
    background_tasks: BackgroundTasks,
) -> Dict:
    """Records that consent was served to a user with a given fides user device id.
    Generally called by the banner or an overlay.

    All items that were served in the same experience should be included in this request body.
    """
    verify_privacy_notice_and_historical_records(
        db=db, notice_history_list=data.privacy_notice_history_ids
    )

    get_privacy_experience_or_error(db, data.privacy_experience_id)

    fides_user_device: Optional[str] = get_fides_user_device_id_from_request(
        data.browser_identity, throw_exception=True
    )

    logger.info("Recording consent served with respect to fides user device id")

    try:
        last_served_record, task_data = save_last_served_and_prep_task_data(
            db=db,
            request=request,
            request_data=data,
            fides_user_device=fides_user_device,
        )

        served: Dict = last_served_record.served or {}
        # Overriding privacy notice history ids on response so previously saved
        # data isn't returned
        served["privacy_notice_history_ids"] = data.privacy_notice_history_ids
        served["served_notice_history_id"] = task_data["served_notice_history_id"]

        background_tasks.add_task(save_consent_served_task, task_data)
        return served

    except (
        IdentityNotFoundException,
        PrivacyNoticeHistoryNotFound,
    ) as exc:
        raise HTTPException(status_code=400, detail=exc.args[0])


def save_last_served_and_prep_task_data(
    db: Session,
    request: Request,
    request_data: RecordConsentServedRequest,
    fides_user_device: Optional[str] = None,
    email: Optional[str] = None,
    phone_number: Optional[str] = None,
) -> Tuple[LastServedNoticeV2, dict]:
    """Upsert the record of the last served consent data for the given user, and pull additional
    data from request headers to later queue for more detailed served notice reporting
    """

    hashed_device: Optional[str] = ConsentIdentitiesMixin.hash_value(fides_user_device)
    hashed_email: Optional[str] = ConsentIdentitiesMixin.hash_value(email)
    hashed_phone: Optional[str] = ConsentIdentitiesMixin.hash_value(phone_number)

    identities_data = ConsentIdentitiesSchema(
        email=email,
        fides_user_device=fides_user_device,
        phone_number=phone_number,
        hashed_email=hashed_email,
        hashed_fides_user_device=hashed_device,
        hashed_phone_number=hashed_phone,
    )

    last_served_notice: LastServedNoticeV2 = save_consent_served_for_identities_v2(
        db=db,
        consent_identity_data=identities_data,
        attributes_served=RecordsServed(**dict(request_data)),
    )

    served_notice_history_id: str = (
        LastServedNoticeV2.generate_served_notice_history_id()
    )

    task_data = prep_served_consent_reporting_task_data(
        request, identities_data, request_data, served_notice_history_id
    )

    return last_served_notice, task_data


class ConsentIdentitiesSchema(FidesSchema):
    """Holds identities for consent reporting save internally"""

    email: Optional[str] = None
    fides_user_device: Optional[str] = None
    phone_number: Optional[str] = None
    hashed_email: Optional[str] = None
    hashed_fides_user_device: Optional[str] = None
    hashed_phone_number: Optional[str] = None


class LastServedSchema(ConsentIdentitiesSchema):
    """Prepares Last Served Data before save, collapsing
    into one record"""

    served: RecordsServed


def consolidate_identities(
    task_data: Dict,
    combined_email: Optional[str],
    combined_phone: Optional[str],
    combined_device: Optional[str],
) -> Dict:
    """Consolidate identities if combining multiple records, rehashing where necessary for further lookup"""
    task_data["email"] = task_data["email"] or combined_email
    task_data["hashed_email"] = ConsentIdentitiesMixin.hash_value(task_data["email"])
    task_data["phone_number"] = task_data["phone_number"] or combined_phone
    task_data["hashed_phone_number"] = ConsentIdentitiesMixin.hash_value(
        task_data["phone_number"]
    )
    task_data["fides_user_device"] = task_data["fides_user_device"] or combined_device
    task_data["hashed_fides_user_device"] = ConsentIdentitiesMixin.hash_value(
        task_data["fides_user_device"]
    )

    return task_data


def save_consent_served_for_identities_v2(
    db: Session,
    consent_identity_data: ConsentIdentitiesSchema,
    attributes_served: RecordsServed,
) -> LastServedNoticeV2:
    """Upsert a LastServedNoticeV2 record for the given user"""

    # Prepare the request data to be in LastServedNoticeV2 format
    data: LastServedSchema = LastServedSchema(
        **consent_identity_data.dict(),
        served=attributes_served.dict(),
    )

    # Fetch records that have any of that matching identifiers in the current request,
    # making it possible to consolidate user records.
    existing_user_records: Query = get_records_with_consent_identifiers(
        db,
        LastServedNoticeV2,
        hashed_device=consent_identity_data.hashed_fides_user_device,
        hashed_email=consent_identity_data.hashed_email,
        hashed_phone=consent_identity_data.hashed_phone_number,
    ).order_by(LastServedNoticeV2.created_at.desc())

    if existing_user_records.first():
        retained_record: LastServedNoticeV2 = existing_user_records.first()  # type: ignore[assignment]
        records_to_delete: List[str] = []

        combined_email: Optional[str] = None
        combined_phone: Optional[str] = None
        combined_device: Optional[str] = None

        # Retain records of Privacy Notices served that are not in the current request.
        combined_notices_served: Set[SafeStr] = set()
        for record in existing_user_records:
            # Combine non-null identifiers, prioritizing more recently used first
            if not combined_email and record.email:
                combined_email = record.email

            if not combined_phone and record.phone_number:
                combined_phone = record.phone_number

            if not combined_device and record.fides_user_device:
                combined_device = record.fides_user_device

            if record.id != retained_record.id:
                records_to_delete.append(record.id)

            # Combine existing privacy notices served
            existing_notices_served: List[SafeStr] = (record.served or {}).get(
                "privacy_notice_history_ids", []
            )
            combined_notices_served.update(existing_notices_served)

        # Now override the combined previous served with the latest served from the request
        combined_notices_served.update(
            attributes_served.privacy_notice_history_ids or []
        )
        attributes_served.privacy_notice_history_ids = list(combined_notices_served)
        data.served = attributes_served

        last_served_data: Dict = data.dict()
        consolidate_identities(
            last_served_data,
            combined_email=combined_email,
            combined_phone=combined_phone,
            combined_device=combined_device,
        )

        retained_record.update(db=db, data=last_served_data)

        # Delete all records except for the consolidated recod
        db.query(LastServedNoticeV2).filter(
            LastServedNoticeV2.id.in_(records_to_delete)
        ).delete()

        record = retained_record

    else:
        record = LastServedNoticeV2.create(db, data=data.dict())

    return record


def prep_served_consent_reporting_task_data(
    request: Request,
    identities: ConsentIdentitiesSchema,
    request_data: RecordConsentServedRequest,
    served_notice_history_id: str,
) -> Dict:
    """Prepare data to pass to background task for more detailed served notice reporting

    Combines data from the original request with user data from request headers. Data must
    be serializable.
    """
    request_headers = request.headers
    ip_address: Optional[str] = anonymize_ip_address(get_ip_address(request))
    user_agent: Optional[str] = request_headers.get("User-Agent")
    url_recorded: Optional[str] = request_headers.get("Referer")

    resp = {
        "acknowledge_mode": request_data.acknowledge_mode,
        "anonymized_ip_address": ip_address,
        "email": identities.email,
        "fides_user_device": identities.fides_user_device,
        "hashed_email": identities.hashed_email,
        "hashed_fides_user_device": identities.hashed_fides_user_device,
        "hashed_phone_number": identities.hashed_phone_number,
        "phone_number": identities.phone_number,
        "privacy_experience_id": request_data.privacy_experience_id or None,
        "served": RecordsServed(**dict(request_data)).dict(),
        "served_notice_history_id": served_notice_history_id,
        "serving_component": request_data.serving_component.value
        if request_data.serving_component
        else None,
        "user_agent": user_agent,
        "user_geography": request_data.user_geography,
        "url_recorded": url_recorded,
    }
    return resp


def save_consent_served_task(task_data: Dict[str, Any]) -> List[ServedNoticeHistoryV2]:
    """
    Task that is queued as a follow-up to saving a quick NoticeServedV2
    resource that builds a more detailed record for served notice reporting.
    """
    with sync_session() as db:
        experience_lookups_for_consent_reporting(db, task_data)
        served = task_data.pop("served", {})

        served_privacy_notice_history_ids = served.pop("privacy_notice_history_ids", [])

        historical_records_created = []

        if served_privacy_notice_history_ids:
            for privacy_notice_history_id in served_privacy_notice_history_ids:
                privacy_notice_history = PrivacyNoticeHistory.get(
                    db=db, object_id=privacy_notice_history_id
                )
                if not privacy_notice_history:
                    continue

                task_data["notice_name"] = privacy_notice_history.name
                task_data["privacy_notice_history_id"] = privacy_notice_history_id
                historical_records_created.append(
                    ServedNoticeHistoryV2.create(
                        db=db,
                        data=task_data,
                    )
                )

        else:
            task_data["notice_name"] = "TCF"
            task_data["tcf_served"] = served
            historical_records_created.append(
                ServedNoticeHistoryV2.create(
                    db=db,
                    data=task_data,
                )
            )

        return historical_records_created


def experience_lookups_for_consent_reporting(
    db: Session, task_data: Dict[str, Any]
) -> Tuple[Optional[str], Optional[str]]:
    """Updates reporting data in place with experience config and request origin if applicable"""
    privacy_experience_id = task_data.get("privacy_experience_id")

    privacy_experience: Optional[PrivacyExperience] = None
    privacy_experience_config_history_id: Optional[str] = None
    request_origin: Optional[str] = None
    if privacy_experience_id:
        privacy_experience = PrivacyExperience.get(
            db=db, object_id=privacy_experience_id
        )

    if privacy_experience:
        experience_config_id = privacy_experience.experience_config_id
        if experience_config_id:
            task_data[
                "privacy_experience_config_history_id"
            ] = privacy_experience.experience_config.experience_config_history_id
            task_data["request_origin"] = privacy_experience.component.value  # type: ignore[attr-defined]

    return privacy_experience_config_history_id, request_origin


def get_fides_user_device_id_from_request(
    identity_data: Optional[Identity], throw_exception: bool = True
) -> Optional[str]:
    """
    Extracts the fides user device id from the request or throws an exception
    """
    if not identity_data or not identity_data.fides_user_device_id:
        if throw_exception:
            raise HTTPException(
                HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Fides user device id not found in identity data",
            )
        return None

    return identity_data.fides_user_device_id
