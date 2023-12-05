import ipaddress
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.params import Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import literal
from sqlalchemy.orm import Query, Session
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from fides.api.api.deps import get_db
from fides.api.custom_types import SafeStr
from fides.api.models.fides_user import FidesUser
from fides.api.models.privacy_notice import PrivacyNotice, PrivacyNoticeHistory
from fides.api.models.privacy_preference import CurrentPrivacyPreference
from fides.api.models.privacy_preference_v2 import PrivacyPreferenceHistoryV2
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.privacy_preference import (
    ConsentReportingSchema,
    CurrentPrivacyPreferenceReportingSchema,
)
from fides.api.util.api_router import APIRouter
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
) -> AbstractPage[PrivacyPreferenceHistoryV2]:
    """Endpoint to return a historical record of all privacy preferences saved for consent reporting v2"""

    validate_start_and_end_filters(
        [(request_timestamp_lt, request_timestamp_gt, "request_timestamp")]
    )

    query: Query[PrivacyPreferenceHistoryV2] = (
        db.query(
            PrivacyPreferenceHistoryV2.id,
            PrivacyRequest.id.label("privacy_request_id"),
            PrivacyPreferenceHistoryV2.email.label("email"),
            PrivacyPreferenceHistoryV2.phone_number.label("phone_number"),
            PrivacyPreferenceHistoryV2.fides_user_device.label("fides_user_device_id"),
            PrivacyPreferenceHistoryV2.secondary_user_ids,
            PrivacyPreferenceHistoryV2.created_at.label("request_timestamp"),
            PrivacyPreferenceHistoryV2.request_origin.label("request_origin"),
            PrivacyRequest.status.label("request_status"),
            literal("consent").label(
                "request_type"
            ),  # Right now, we know this is consent, so hardcoding to avoid the Policy/Rule join
            FidesUser.username.label("approver_id"),
            PrivacyPreferenceHistoryV2.privacy_notice_history_id.label(
                "privacy_notice_history_id"
            ),
            PrivacyPreferenceHistoryV2.preference.label("preference"),
            PrivacyPreferenceHistoryV2.user_geography.label("user_geography"),
            PrivacyPreferenceHistoryV2.relevant_systems.label("relevant_systems"),
            PrivacyPreferenceHistoryV2.affected_system_status.label(
                "affected_system_status"
            ),
            PrivacyPreferenceHistoryV2.url_recorded.label("url_recorded"),
            PrivacyPreferenceHistoryV2.user_agent.label("user_agent"),
            PrivacyPreferenceHistoryV2.privacy_experience_id.label(
                "privacy_experience_id"
            ),
            PrivacyPreferenceHistoryV2.privacy_experience_config_history_id.label(
                "experience_config_history_id"
            ),
            PrivacyPreferenceHistoryV2.anonymized_ip_address.label(
                "truncated_ip_address"
            ),
            PrivacyPreferenceHistoryV2.method.label("method"),
            PrivacyPreferenceHistoryV2.served_notice_history_id.label(
                "served_notice_history_id"
            ),
            PrivacyPreferenceHistoryV2.tcf_preferences.label("tcf_preferences"),
        )
        .outerjoin(
            PrivacyRequest,
            PrivacyRequest.id == PrivacyPreferenceHistoryV2.privacy_request_id,
        )
        .outerjoin(FidesUser, PrivacyRequest.reviewed_by == FidesUser.id)
    )

    if request_timestamp_lt:
        query = query.filter(
            PrivacyPreferenceHistoryV2.created_at < request_timestamp_lt
        )
    if request_timestamp_gt:
        query = query.filter(
            PrivacyPreferenceHistoryV2.created_at > request_timestamp_gt
        )

    query = query.order_by(PrivacyPreferenceHistoryV2.created_at.desc())

    return paginate(query, params)
