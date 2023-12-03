from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, Depends, HTTPException, Request, Response
from loguru import logger
from sqlalchemy.orm import Query, Session
from starlette.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_ENTITY

from fides.api.api.deps import get_db
from fides.api.api.v1.endpoints.privacy_preference_endpoints import (
    anonymize_ip_address,
    get_ip_address,
    verify_privacy_notice_and_historical_records,
)
from fides.api.common_exceptions import (
    IdentityNotFoundException,
    PrivacyNoticeHistoryNotFound,
    SystemNotFound,
)
from fides.api.db.ctl_session import sync_session
from fides.api.models.privacy_experience import PrivacyExperience
from fides.api.models.privacy_notice import PrivacyNoticeHistory
from fides.api.models.privacy_preference_v2 import (
    ConsentIdentitiesMixin,
    LastServedNoticeV2,
    ServedNoticeHistoryV2,
    get_records_with_consent_identifiers,
)
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_preference import RecordConsentServedRequest
from fides.api.schemas.privacy_preference_v2 import RecordsServed, RecordsServedResponse
from fides.api.schemas.redis_cache import Identity
from fides.api.util.api_router import APIRouter
from fides.api.util.endpoint_utils import fides_limiter
from fides.common.api.v1.urn_registry import NOTICES_SERVED, V1_URL_PREFIX
from fides.config import CONFIG

router = APIRouter(tags=["Privacy Preference"], prefix=V1_URL_PREFIX)


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
) -> RecordsServedResponse:
    """Records that consent was served to a user with a given fides user device id.
    Generally called by the banner or an overlay.

    All items that were served in the same experience should be included in this request body.
    """
    verify_privacy_notice_and_historical_records(
        db=db, notice_history_list=data.privacy_notice_history_ids
    )

    fides_user_device: str = get_fides_user_device_id_from_request(
        data.browser_identity
    )

    logger.info("Recording consent served with respect to fides user device id")

    try:
        last_served_record, task_data = save_last_served_and_prep_task_data(
            db=db,
            request=request,
            request_data=data,
            fides_user_device=fides_user_device,
        )

        served = last_served_record.served
        # Overriding privacy notice history ids on response so previously saved
        # data isn't returned
        served["privacy_notice_history_ids"] = data.privacy_notice_history_ids
        served["served_notice_history_id"] = task_data["served_notice_history_id"]

        background_tasks.add_task(save_consent_served_task, task_data)
        return served

    except (
        IdentityNotFoundException,
        PrivacyNoticeHistoryNotFound,
        SystemNotFound,
    ) as exc:
        raise HTTPException(status_code=400, detail=exc.args[0])


def save_last_served_and_prep_task_data(
    db: Session,
    request: Request,
    request_data: RecordConsentServedRequest,
    fides_user_device: Optional[str] = None,
    email: Optional[str] = None,
    phone_number: Optional[str] = None,
):
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
        attributes_served=request_data.dict(
            include=set(RecordsServed.__annotations__.keys())
        ),
    )

    served_notice_history_id: str = (
        LastServedNoticeV2.generate_served_notice_history_id()
    )

    task_data = prep_served_consent_reporting_task_data(
        request, served_notice_history_id, identities_data, request_data
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

    served: RecordsServed = {}


def save_consent_served_for_identities_v2(
    db: Session,
    consent_identity_data: ConsentIdentitiesSchema,
    attributes_served: Dict[str, List],
) -> LastServedNoticeV2:
    data = LastServedSchema(
        **consent_identity_data.dict(),
        served=attributes_served,
    )

    existing_user_records: Query = get_records_with_consent_identifiers(
        db,
        LastServedNoticeV2,
        hashed_device=consent_identity_data.hashed_fides_user_device,
        hashed_email=consent_identity_data.hashed_email,
        hashed_phone=consent_identity_data.hashed_phone_number,
    )

    if existing_user_records.count():
        retained_record = existing_user_records.first()
        records_to_delete: List[int] = []

        combined_notices_served = set()
        for record in existing_user_records:
            if record.id != retained_record.id:
                records_to_delete.append(record.id)

            # Combine existing privacy notices served
            existing_notices_served: List[int] = (record.served or {}).get(
                "privacy_notice_history_ids", []
            )
            combined_notices_served.update(existing_notices_served)

        combined_notices_served.update(
            attributes_served.get("privacy_notice_history_ids")
        )
        attributes_served["privacy_notice_history_ids"] = list(combined_notices_served)

        data.served = attributes_served

        retained_record.update(db=db, data=data.dict())

        db.query(LastServedNoticeV2).filter(
            LastServedNoticeV2.id.in_(records_to_delete)
        ).delete()
        record = retained_record

    else:
        record = LastServedNoticeV2.create(db, data=data.dict())

    return record


def prep_served_consent_reporting_task_data(
    request: Request,
    served_notice_history_id: str,
    identities: ConsentIdentitiesSchema,
    request_data: RecordConsentServedRequest,
) -> Dict:
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


def save_consent_served_task(task_data: Dict[str, Any]):
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


def experience_lookups_for_consent_reporting(db: Session, task_data: Dict[str, Any]):
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
            task_data["request_origin"] = privacy_experience.component.value

    return privacy_experience_config_history_id, request_origin


def get_fides_user_device_id_from_request(
    identity_data: Optional[Identity],
) -> str:
    """
    Extracts the fides user device id from the request or throws an exception
    """
    if not identity_data or not identity_data.fides_user_device_id:
        raise HTTPException(
            HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fides user device id not found in identity data",
        )

    return identity_data.fides_user_device_id
