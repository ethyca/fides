import argparse
from datetime import datetime, timedelta
from typing import Optional, Tuple, Type, Union
from uuid import uuid4

import pandas as pd
from loguru import logger
from pandas import DataFrame
from sqlalchemy.orm import Query, Session

from fides.api.db.seed import DEFAULT_CONSENT_POLICY
from fides.api.db.session import get_db_session
from fides.api.models.policy import Policy
from fides.api.models.privacy_experience import ComponentType, PrivacyExperience
from fides.api.models.privacy_notice import PrivacyNotice, PrivacyNoticeRegion
from fides.api.models.privacy_preference import (
    DeprecatedCurrentPrivacyPreference,
    DeprecatedLastServedNotice,
    DeprecatedPrivacyPreferenceHistory,
    DeprecatedServedNoticeHistory,
)
from fides.api.models.privacy_preference_v2 import (
    PrivacyPreferenceHistoryV2,
    ServedNoticeHistoryV2, CurrentPrivacyPreferenceV2,
)
from fides.api.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestStatus,
    ProvidedIdentity,
)
from fides.config import CONFIG

device_id: str = "051b219f-20e4-45df-82f7-5eb68a00889f"
hashed_device: str = ProvidedIdentity.hash_value(device_id)
email: str = "customer_1_fides_test@example.com"
hashed_email: str = ProvidedIdentity.hash_value(email)
phone_number: str = "+15308675309"
hashed_phone: str = ProvidedIdentity.hash_value(hashed_email)
secondary_user_ids = {"ga_client_id": "ga_example_1"}
affected_system_status = {"test_system_fides_key": "complete"}
anonymized_ip = "92.158.1.0"
url_recorded = "https://example.com/homepage"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24"
geography = "us_ca"


def verify_current_preference(identifier: str):
    current_preference_query = db.query(CurrentPrivacyPreferenceV2).filter(CurrentPrivacyPreferenceV2.id == identifier)

    print_records_in_dataframe(CurrentPrivacyPreferenceV2, current_preference_query)


def verify_migrated_historical_record(old_record_type: Union[Type[DeprecatedServedNoticeHistory], Type[DeprecatedPrivacyPreferenceHistory]], new_record_type: Union[Type[PrivacyPreferenceHistoryV2], Type[ServedNoticeHistoryV2]], identifier: str):
    logger.info(f"Verifying {str(old_record_type)} -> {str(new_record_type)} migration")
    original_record: Optional[Union[DeprecatedServedNoticeHistory, DeprecatedPrivacyPreferenceHistory]] = db.query(old_record_type).get(identifier)
    migrated_record: Optional[Union[ServedNoticeHistoryV2, PrivacyPreferenceHistoryV2]] = db.query(new_record_type).get(identifier)

    assert migrated_record

    for col in new_record_type.__table__.columns.keys():
        new_val = getattr(migrated_record, col, None)
        old_val = getattr(original_record, col, None)
        if new_val != old_val:
            print(f"Mismatch: Column {col}. Old val: {old_val}, New val: {new_val}")

    new_records: Query = db.query(new_record_type).filter(new_record_type.id == identifier)
    pd.set_option("max_colwidth", 400)

    print(f"Migrated {str(new_record_type)}")
    df: DataFrame = pd.read_sql(
        new_records.statement, con=db.bind, columns=new_record_type.__table__.columns.keys()
    )
    df_transposed = df.T
    print(df_transposed)

def print_records_in_dataframe(record_type, query):
    pd.set_option("max_colwidth", 600)

    print(f"Migrated {str(record_type)}")
    df: DataFrame = pd.read_sql(
        query.statement, con=db.bind, columns=record_type.__table__.columns.keys()
    )
    df_transposed = df.T
    print(df_transposed)


def create_test_privacy_request(
    db: Session,
) -> PrivacyRequest:
    """Create a fake privacy request to attach to a DeprecatedPrivacyPreferenceHistory record for testing"""
    consent_policy: Policy = (
        db.query(Policy).filter(Policy.key == DEFAULT_CONSENT_POLICY).first()
    )

    return PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid4())}",
            "started_processing_at": datetime.utcnow(),
            "requested_at": datetime.utcnow() - timedelta(days=1),
            "status": PrivacyRequestStatus.in_processing,
            "origin": f"https://example.com//",
            "policy_id": consent_policy.id,
        },
    )


def create_fides_user_device_provided_identity(
    db: Session
) -> ProvidedIdentity:
    """Create a fides user device provided identity for testing"""
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "fides_user_device_id",
        "hashed_value": hashed_device,
        "encrypted_value": {"value": device_id},
    }
    return ProvidedIdentity.create(db, data=provided_identity_data)


def create_email_provided_identity(
    db: Session
) -> ProvidedIdentity:
    """Create an email provided identity for testing"""
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "email",
        "hashed_value": hashed_email,
        "encrypted_value": {"value": email},
    }
    return ProvidedIdentity.create(db, data=provided_identity_data)


def create_phone_provided_identity(
    db: Session
) -> ProvidedIdentity:
    """Create an phone provided identity for testing"""
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "phone_number",
        "hashed_value": hashed_phone,
        "encrypted_value": {"value": phone_number},
    }
    return ProvidedIdentity.create(db, data=provided_identity_data)


def get_us_ca_notice_and_history_id(db: Session) -> Tuple[str, str]:
    """Fetch the out of the box CA Data Sales and Sharing notice id, and a historical id for testing"""

    privacy_notice = (
        db.query(PrivacyNotice)
        .filter(PrivacyNotice.regions.any(PrivacyNoticeRegion.us_ca.value))
        .first()
    )
    return privacy_notice.id, privacy_notice.histories[0].id


def create_current_records(db, served_history: DeprecatedServedNoticeHistory, preference_history: DeprecatedPrivacyPreferenceHistory):
    provided_identity = create_email_provided_identity(db)

    fides_user_device_provided_identity = create_fides_user_device_provided_identity(db)

    notice_id, notice_history_id = get_us_ca_notice_and_history_id(db)

    current_pref = DeprecatedCurrentPrivacyPreference.create(db, data={
        "preference": "opt_in",
        "provided_identity_id": provided_identity.id,
        "privacy_notice_id": notice_id,
        "privacy_notice_history_id": notice_history_id,
        "privacy_preference_history_id": preference_history.id,
        "fides_user_device_provided_identity_id": fides_user_device_provided_identity.id,
    })
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    current_served = DeprecatedLastServedNotice.create(db, data={
        "served_notice_history_id": served_history.id,
        "provided_identity_id": provided_identity.id,
        "fides_user_device_provided_identity_id": fides_user_device_provided_identity.id,
        "privacy_notice_id": notice_id,
        "privacy_notice_history_id": notice_history_id,
    })

    logger.info(f"Created DeprecatedLastServedNotice with id={current_served.id}")



def create_historical_records(db):
    """Created DeprecatedPrivacyPreferenceHistory and DeprecatedServedNoticeHistory records for migration testing"""
    notice_id, notice_history_id = get_us_ca_notice_and_history_id(db)

    fides_device_provided_identity: ProvidedIdentity = (
        create_fides_user_device_provided_identity(db)
    )

    privacy_request: PrivacyRequest = create_test_privacy_request(db)

    ca_overlay_experience: PrivacyExperience = (
        PrivacyExperience.get_experience_by_region_and_component(
            db, component=ComponentType.overlay, region=PrivacyNoticeRegion.us_ca
        )
    )

    common_data = {
        "anonymized_ip_address": anonymized_ip,
        "email": email,
        "hashed_email": hashed_email,
        "hashed_phone_number": hashed_phone,
        "phone_number": phone_number,
        "fides_user_device": device_id,
        "hashed_fides_user_device": hashed_device,
        "fides_user_device_provided_identity_id": fides_device_provided_identity.id,
        "privacy_experience_config_history_id": ca_overlay_experience.experience_config.experience_config_history_id,
        "privacy_experience_id": ca_overlay_experience.id,
        "request_origin": "overlay",
        "user_agent": user_agent,
        "user_geography": geography,
        "url_recorded": url_recorded,
        "privacy_notice_history_id": notice_history_id,
    }

    served_history = DeprecatedServedNoticeHistory.create(
        db=db,
        data={
            **{
                "acknowledge_mode": False,
                "serving_component": "overlay",
            },
            **common_data,
        },
        check_name=False,
    )
    logger.info(f"Created DeprecatedServedNoticeHistory with id={served_history.id}")

    preference_history_record = DeprecatedPrivacyPreferenceHistory.create(
        db=db,
        data={
            **{
                "affected_system_status": affected_system_status,
                "method": "button",
                "preference": "opt_out",
                "privacy_request_id": privacy_request.id,
                "relevant_systems": ["test_system_fides_key"],
                "secondary_user_ids": secondary_user_ids,
                "served_notice_history_id": served_history.id,
            },
            **common_data,
        },
        check_name=False,
    )
    logger.info(
        f"Created DeprecatedPrivacyPreferenceHistory with id={preference_history_record.id}"
    )

    return served_history, preference_history_record


if __name__ == "__main__":
    SessionLocal = get_db_session(CONFIG)
    db = SessionLocal()

    parser = argparse.ArgumentParser(
        description="Create resources and verify migration of Privacy Preferences V2"
    )

    parser.add_argument("--historical_preference", type=str, default=None)
    parser.add_argument("--historical_served", type=str, default=None)
    parser.add_argument("--current_preference", type=str, default=None)


    args = parser.parse_args()

    privacy_preference_id = args.historical_preference
    historical_served = args.historical_served
    current_preference = args.current_preference

    if privacy_preference_id or historical_served or current_preference:
        if privacy_preference_id:
            verify_migrated_historical_record(
                old_record_type=DeprecatedPrivacyPreferenceHistory,
                new_record_type=PrivacyPreferenceHistoryV2,
                identifier=privacy_preference_id,
            )
        if historical_served:
            verify_migrated_historical_record(
                old_record_type=DeprecatedServedNoticeHistory,
                new_record_type=ServedNoticeHistoryV2,
                identifier=historical_served,
            )
        if current_preference:
            verify_current_preference(
                identifier=current_preference
            )
    else:
        served_history, preference_history = create_historical_records(db)
        create_current_records(db, served_history, preference_history)
    db.close()
