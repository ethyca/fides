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
)
from fides.api.models.privacy_preference_v2 import (
    PrivacyPreferenceHistory,
    ServedNoticeHistory, CurrentPrivacyPreferenceV2,
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


def verify_current_preference():

    current_preference_query = db.query(CurrentPrivacyPreferenceV2)

    print_records_in_dataframe(CurrentPrivacyPreferenceV2, current_preference_query, transposed=False)


def verify_migrated_historical_record(new_record_type: Union[Type[PrivacyPreferenceHistory], Type[ServedNoticeHistory]], identifier: str):
    logger.info(f"Verifying {str(new_record_type)} migration")

    new_records: Query = db.query(new_record_type).filter(new_record_type.id == identifier)

    print_records_in_dataframe(new_record_type, new_records, transposed=True)


def print_records_in_dataframe(record_type, query, transposed: bool = True):
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", None)

    print(f"Migrated {str(record_type)}")
    df: DataFrame = pd.read_sql(
        query.statement, con=db.bind, columns=record_type.__table__.columns.keys()
    )
    df['created_at'] = df['created_at'].dt.tz_localize(None)
    df['updated_at'] = df['updated_at'].dt.tz_localize(None)

    file_name = f'{str(record_type)}_validation'
    # saving the excel
    df.to_excel(file_name)

    df_transposed = df
    if transposed:
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
    db: Session, fides_device_id
) -> ProvidedIdentity:
    """Create a fides user device provided identity for testing"""

    hashed: str = ProvidedIdentity.hash_value(fides_device_id)

    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "fides_user_device_id",
        "hashed_value": hashed,
        "encrypted_value": {"value": fides_device_id},
    }
    return ProvidedIdentity.create(db, data=provided_identity_data)


def create_email_provided_identity(
    db: Session, provided_email
) -> ProvidedIdentity:
    """Create an email provided identity for testing"""
    hashed: str = ProvidedIdentity.hash_value(provided_email)

    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "email",
        "hashed_value": hashed,
        "encrypted_value": {"value": provided_email},
    }
    return ProvidedIdentity.create(db, data=provided_identity_data)


def create_phone_provided_identity(
    db: Session, provided_phone_number
) -> ProvidedIdentity:
    """Create an phone provided identity for testing"""
    hashed: str = ProvidedIdentity.hash_value(provided_phone_number)


    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "phone_number",
        "hashed_value": hashed,
        "encrypted_value": {"value": provided_phone_number},
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


def get_essential_notice_and_history_id(db: Session) -> Tuple[str, str]:
    """Fetch the out of the box Essential notice id, and a historical id for testing"""

    privacy_notice = (
        db.query(PrivacyNotice)
        .filter(PrivacyNotice.notice_key == "essential")
        .first()
    )
    return privacy_notice.id, privacy_notice.histories[0].id


def get_functional_notice_and_history_id(db: Session) -> Tuple[str, str]:
    """Fetch the out of the box functional notice id, and a historical id for testing"""

    privacy_notice = (
        db.query(PrivacyNotice)
        .filter(PrivacyNotice.notice_key == "functional")
        .first()
    )
    return privacy_notice.id, privacy_notice.histories[0].id



def create_current_records(db):

    provided_identity = create_email_provided_identity(db, "dawn@example.com")
    fides_user_device_provided_identity = create_fides_user_device_provided_identity(db, "dawn119f-20e4-45df-82f7-5eb68a00889f")
    newer_fides_device = create_fides_user_device_provided_identity(db, "dawn219f-20e4-45df-82f7-5eb68a00889f")
    phone_provided_identity = create_phone_provided_identity(db, "+15555555555")

    notice_id, notice_history_id = get_us_ca_notice_and_history_id(db)
    functional_notice_id, functional_notice_history_id = get_functional_notice_and_history_id(db)
    essential_notice_id, essential_notice_history_id = get_essential_notice_and_history_id(db)

    # Dawn opted in to CA notice under email and device id
    current_pref = DeprecatedCurrentPrivacyPreference.create(db, data={
        "preference": "opt_in",
        "provided_identity_id": provided_identity.id,
        "privacy_notice_id": notice_id,
        "privacy_notice_history_id": notice_history_id,
        "fides_user_device_provided_identity_id": fides_user_device_provided_identity.id,
    })
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    # Dawn opted out of function notice under matching device id
    current_pref = DeprecatedCurrentPrivacyPreference.create(db, data={
        "preference": "opt_out",
        "provided_identity_id": None,
        "privacy_notice_id": functional_notice_id,
        "privacy_notice_history_id": functional_notice_history_id,
        "fides_user_device_provided_identity_id": fides_user_device_provided_identity.id,
    })
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    # Dawn opted in to essential_notice_id notice under phone and matching device id
    current_pref = DeprecatedCurrentPrivacyPreference.create(db, data={
        "preference": "opt_in",
        "provided_identity_id": phone_provided_identity.id,
        "privacy_notice_id": essential_notice_id,
        "privacy_notice_history_id": essential_notice_history_id,
        "fides_user_device_provided_identity_id": fides_user_device_provided_identity.id,
    })
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    # Dawn opted out of CA notice under phone and newer device id
    current_pref = DeprecatedCurrentPrivacyPreference.create(db, data={
        "preference": "opt_out",
        "provided_identity_id": phone_provided_identity.id,
        "privacy_notice_id": notice_id,
        "privacy_notice_history_id": notice_history_id,
        "fides_user_device_provided_identity_id": newer_fides_device.id
    })
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    # Jane's identifiers
    jane_provided_identity = create_email_provided_identity(db, "jane@example.com")
    jane_fides_user_device_provided_identity = create_fides_user_device_provided_identity(db, "jane119f-20e4-45df-82f7-5eb68a00889f")

    # Jane opted out of CA notice under email
    current_pref = DeprecatedCurrentPrivacyPreference.create(db, data={
        "preference": "opt_out",
        "provided_identity_id": jane_provided_identity.id,
        "privacy_notice_id": notice_id,
        "privacy_notice_history_id": notice_history_id,
        "fides_user_device_provided_identity_id": None,
    })
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    # Jane opted into essential notice under email and device id
    current_pref = DeprecatedCurrentPrivacyPreference.create(db, data={
        "preference": "opt_in",
        "provided_identity_id": jane_provided_identity.id,
        "privacy_notice_id": essential_notice_id,
        "privacy_notice_history_id": essential_notice_history_id,
        "fides_user_device_provided_identity_id": jane_fides_user_device_provided_identity.id,
    })
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    # Joe's identifiers
    joe_fides_device = create_fides_user_device_provided_identity(db, "joe1219f-20e4-45df-82f7-5eb68a00889f")

    # Joe opted out of essential notice under device
    current_pref = DeprecatedCurrentPrivacyPreference.create(db, data={
        "preference": "opt_out",
        "provided_identity_id": None,
        "privacy_notice_id": essential_notice_id,
        "privacy_notice_history_id": essential_notice_history_id,
        "fides_user_device_provided_identity_id": joe_fides_device.id,
    })
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    # Elizabeth's identifiers
    elizabeth_phone_provided_identity = create_phone_provided_identity(db, "+6666666666")

    # Elizabeth opted out of functional notices under phone number
    current_pref = DeprecatedCurrentPrivacyPreference.create(db, data={
        "preference": "opt_out",
        "provided_identity_id": elizabeth_phone_provided_identity.id,
        "privacy_notice_id": functional_notice_id,
        "privacy_notice_history_id": functional_notice_history_id,
        "fides_user_device_provided_identity_id": None,
    })
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    current_served = DeprecatedLastServedNotice.create(db, data={
        "provided_identity_id": provided_identity.id,
        "fides_user_device_provided_identity_id": fides_user_device_provided_identity.id,
        "privacy_notice_id": notice_id,
        "privacy_notice_history_id": notice_history_id,
    })

    logger.info(f"Created DeprecatedLastServedNotice with id={current_served.id}")


def create_historical_records(db):
    """Created PrivacyPreferenceHistory and ServedNoticeHistory records for migration testing"""
    notice_id, notice_history_id = get_us_ca_notice_and_history_id(db)

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
        "privacy_experience_config_history_id": ca_overlay_experience.experience_config.experience_config_history_id,
        "privacy_experience_id": ca_overlay_experience.id,
        "request_origin": "overlay",
        "user_agent": user_agent,
        "user_geography": geography,
        "url_recorded": url_recorded,
        "privacy_notice_history_id": notice_history_id,
    }

    served_history = ServedNoticeHistory.create(
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
    logger.info(f"Created ServedNoticeHistory with id={served_history.id}")

    preference_history_record = PrivacyPreferenceHistory.create(
        db=db,
        data={
            **{
                "affected_system_status": affected_system_status,
                "method": "button",
                "preference": "opt_out",
                "privacy_request_id": privacy_request.id,
                "secondary_user_ids": secondary_user_ids,
                "served_notice_history_id": served_history.id,
            },
            **common_data,
        },
        check_name=False,
    )
    logger.info(
        f"Created PrivacyPreferenceHistory with id={preference_history_record.id}"
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
    parser.add_argument("--current_preference", action='store_true')

    args = parser.parse_args()

    privacy_preference_id = args.historical_preference
    historical_served = args.historical_served
    current_preference = args.current_preference

    if privacy_preference_id or historical_served or current_preference:
        if privacy_preference_id:
            verify_migrated_historical_record(
                new_record_type=PrivacyPreferenceHistory,
                identifier=privacy_preference_id,
            )
        if historical_served:
            verify_migrated_historical_record(
                new_record_type=ServedNoticeHistory,
                identifier=historical_served,
            )
        if current_preference:
            verify_current_preference()
    else:
        served_history, preference_history = create_historical_records(db)
        create_current_records(db)
    db.close()
