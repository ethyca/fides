"""
This script is designed to help with testing the Data Migration script
for migrating privacy preferences

The steps to run the script are as follows:
1. In a terminal, run `nox -s teardown -- volumes ; nox -s dev -- shell` to get the server running
3. You can run `python scripts/verify_privacy_preferences_overhaul_migration.py -h` to understand how to invoke script
"""
import argparse
from datetime import datetime, timedelta
from typing import Tuple
from uuid import uuid4

from alembic import command
from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.db.database import get_alembic_config
from fides.api.db.seed import DEFAULT_CONSENT_POLICY
from fides.api.db.session import get_db_session
from fides.api.models.policy import Policy
from fides.api.models.privacy_experience import ComponentType, PrivacyExperience
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    PrivacyNotice,
    PrivacyNoticeHistory,
    PrivacyNoticeRegion,
)
from fides.api.models.privacy_preference import (
    DeprecatedCurrentPrivacyPreference,
    DeprecatedLastServedNotice,
)
from fides.api.models.privacy_preference_v2 import (
    CurrentPrivacyPreferenceV2,
    LastServedNoticeV2,
    PrivacyPreferenceHistory,
    ServedNoticeHistory,
)
from fides.api.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestStatus,
    ProvidedIdentity,
)
from fides.config import CONFIG

secondary_user_ids = {"ga_client_id": "ga_example_1"}
affected_system_status = {"test_system_fides_key": "complete"}
anonymized_ip = "92.158.1.0"
url_recorded = "https://example.com/homepage"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24"
geography = "us_ca"


DATABASE_URL = CONFIG.database.sync_database_uri
AUTH_HEADER = CONFIG.user.auth_header
SERVER_URL = CONFIG.cli.server_url
DOWN_REVISION = "f9b28f36b53e"

print(f"Using Server URL: {SERVER_URL}")


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


def create_email_provided_identity(db: Session, provided_email) -> ProvidedIdentity:
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
        db.query(PrivacyNotice).filter(PrivacyNotice.notice_key == "essential").first()
    )
    return privacy_notice.id, privacy_notice.histories[0].id


def get_functional_notice_and_history_id(db: Session) -> Tuple[str, str]:
    """Fetch the out of the box functional notice id, and a historical id for testing"""

    privacy_notice = (
        db.query(PrivacyNotice).filter(PrivacyNotice.notice_key == "functional").first()
    )
    return privacy_notice.id, privacy_notice.histories[0].id


def create_historical_records(db: Session):
    """Created PrivacyPreferenceHistory and ServedNoticeHistory records for migration testing"""
    notice_id, notice_history_id = get_us_ca_notice_and_history_id(db)

    privacy_request: PrivacyRequest = create_test_privacy_request(db)

    ca_overlay_experience: PrivacyExperience = (
        PrivacyExperience.get_experience_by_region_and_component(
            db, component=ComponentType.overlay, region=PrivacyNoticeRegion.us_ca
        )
    )

    device_id: str = "051b219f-20e4-45df-82f7-5eb68a00889f"
    hashed_device: str = ProvidedIdentity.hash_value(device_id)
    email: str = "customer_1_fides_test@example.com"
    hashed_email: str = ProvidedIdentity.hash_value(email)
    phone_number: str = "+15308675309"
    hashed_phone: str = ProvidedIdentity.hash_value(hashed_email)

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

    # Mimicking TCF record - tcf columns have already been removed
    common_data["privacy_notice_history_id"] = None

    ServedNoticeHistory.create(
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

    # Fake TCF record (one without a privacy notice history id)
    PrivacyPreferenceHistory.create(
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

    return served_history, preference_history_record


def create_current_privacy_preferences(db: Session):
    """Create current privacy preferences"""

    provided_identity = create_email_provided_identity(db, "dawn@example.com")
    fides_user_device_provided_identity = create_fides_user_device_provided_identity(
        db, "dawn119f-20e4-45df-82f7-5eb68a00889f"
    )
    newer_fides_device = create_fides_user_device_provided_identity(
        db, "dawn219f-20e4-45df-82f7-5eb68a00889f"
    )
    phone_provided_identity = create_phone_provided_identity(db, "+15555555555")

    notice_id, notice_history_id = get_us_ca_notice_and_history_id(db)
    (
        functional_notice_id,
        functional_notice_history_id,
    ) = get_functional_notice_and_history_id(db)
    (
        essential_notice_id,
        essential_notice_history_id,
    ) = get_essential_notice_and_history_id(db)

    # Dawn opted in to CA notice under email and device id
    current_pref = DeprecatedCurrentPrivacyPreference.create(
        db,
        data={
            "preference": "opt_in",
            "provided_identity_id": provided_identity.id,
            "privacy_notice_id": notice_id,
            "privacy_notice_history_id": notice_history_id,
            "fides_user_device_provided_identity_id": fides_user_device_provided_identity.id,
        },
    )
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    # Dawn opted out of functional notice under matching device id
    current_pref = DeprecatedCurrentPrivacyPreference.create(
        db,
        data={
            "preference": "opt_out",
            "provided_identity_id": None,
            "privacy_notice_id": functional_notice_id,
            "privacy_notice_history_id": functional_notice_history_id,
            "fides_user_device_provided_identity_id": fides_user_device_provided_identity.id,
        },
    )
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    # Dawn opted in to essential_notice_id notice under phone and matching device id
    current_pref = DeprecatedCurrentPrivacyPreference.create(
        db,
        data={
            "preference": "opt_in",
            "provided_identity_id": phone_provided_identity.id,
            "privacy_notice_id": essential_notice_id,
            "privacy_notice_history_id": essential_notice_history_id,
            "fides_user_device_provided_identity_id": fides_user_device_provided_identity.id,
        },
    )
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    jane_provided_identity = create_email_provided_identity(db, "jane@example.com")
    jane_fides_user_device_provided_identity = (
        create_fides_user_device_provided_identity(
            db, "jane119f-20e4-45df-82f7-5eb68a00889f"
        )
    )

    # Jane opted out of CA notice under email
    current_pref = DeprecatedCurrentPrivacyPreference.create(
        db,
        data={
            "preference": "opt_out",
            "provided_identity_id": jane_provided_identity.id,
            "privacy_notice_id": notice_id,
            "privacy_notice_history_id": notice_history_id,
            "fides_user_device_provided_identity_id": None,
        },
    )
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    # Jane opted into essential notice under email and device id
    current_pref = DeprecatedCurrentPrivacyPreference.create(
        db,
        data={
            "preference": "opt_in",
            "provided_identity_id": jane_provided_identity.id,
            "privacy_notice_id": essential_notice_id,
            "privacy_notice_history_id": essential_notice_history_id,
            "fides_user_device_provided_identity_id": jane_fides_user_device_provided_identity.id,
        },
    )
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    joe_fides_device = create_fides_user_device_provided_identity(
        db, "joe1219f-20e4-45df-82f7-5eb68a00889f"
    )

    # Joe opted out of essential notice under device
    current_pref = DeprecatedCurrentPrivacyPreference.create(
        db,
        data={
            "preference": "opt_out",
            "provided_identity_id": None,
            "privacy_notice_id": essential_notice_id,
            "privacy_notice_history_id": essential_notice_history_id,
            "fides_user_device_provided_identity_id": joe_fides_device.id,
        },
    )
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    elizabeth_phone_provided_identity = create_phone_provided_identity(
        db, "+6666666666"
    )

    # Elizabeth opted out of functional notices under phone number
    current_pref = DeprecatedCurrentPrivacyPreference.create(
        db,
        data={
            "preference": "opt_out",
            "provided_identity_id": elizabeth_phone_provided_identity.id,
            "privacy_notice_id": functional_notice_id,
            "privacy_notice_history_id": functional_notice_history_id,
            "fides_user_device_provided_identity_id": None,
        },
    )
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")

    # Dawn opted out of CA notice under phone and newer device id
    current_pref = DeprecatedCurrentPrivacyPreference.create(
        db,
        data={
            "preference": "opt_out",
            "provided_identity_id": phone_provided_identity.id,
            "privacy_notice_id": notice_id,
            "privacy_notice_history_id": notice_history_id,
            "fides_user_device_provided_identity_id": newer_fides_device.id,
        },
    )
    logger.info(f"Created DeprecatedCurrentPrivacyPreference with id={current_pref.id}")


def reload_objects(db: Session) -> None:
    """
    Downgrades the database to the previous migration,
    loads the "outdated" objects into the database, and then
    migrates back up to 'head'
    """
    alembic_config = get_alembic_config(DATABASE_URL)

    print(f"> Rolling back one migration to: {DOWN_REVISION}")
    command.downgrade(alembic_config, DOWN_REVISION)

    input("> Press Enter to delete Privacy Preference and Notice Served Records... ")

    val = input("> Are you sure you want to delete existing data (Y/N) ? ")
    if val.upper() == "Y":
        delete_old_records(db)
    else:
        print("Exiting migration test.")
        exit()

    print(
        "> Seeding the database Privacy Preference History, Served Notice History, Current Privacy Preference, and Last Served Notice objects"
    )
    create_outdated_objects(db=db)

    print("Upgrading database to migration revision: head")
    command.upgrade(alembic_config, "head")


def create_outdated_objects(db: Session) -> None:
    create_historical_records(db)
    create_current_privacy_preferences(db)


def delete_old_records(db: Session) -> None:
    print("Deleting all Preferences Saved and Notices Served records")
    db.query(DeprecatedCurrentPrivacyPreference).delete()
    db.query(DeprecatedLastServedNotice).delete()
    db.query(PrivacyPreferenceHistory).delete()
    db.query(ServedNoticeHistory).delete()
    db.query(LastServedNoticeV2).delete()
    db.query(CurrentPrivacyPreferenceV2).delete()


def verify_migration(db: Session) -> None:
    """
    Run a battery of assertions to verify the data migration worked as intended.
    """
    privacy_preference_histories: Query = db.query(PrivacyPreferenceHistory)
    assert privacy_preference_histories.count() == 1

    privacy_preference_history = privacy_preference_histories.first()
    privacy_notice_history = (
        db.query(PrivacyNoticeHistory)
        .filter(
            PrivacyNoticeHistory.id
            == privacy_preference_history.privacy_notice_history_id
        )
        .first()
    )
    db.refresh(privacy_preference_history)

    assert (
        privacy_preference_history.notice_name
        == privacy_notice_history.name
        == "Data Sales and Sharing"
    )
    assert (
        privacy_preference_history.notice_key
        == privacy_notice_history.notice_key
        == "data_sales_and_sharing"
    )
    assert (
        privacy_preference_history.notice_mechanism
        == privacy_notice_history.consent_mechanism
        == ConsentMechanism.opt_out
    )

    print("> Verified Privacy Preference History migration.")

    served_notice_histories: Query = db.query(ServedNoticeHistory)
    assert privacy_preference_histories.count() == 1

    served_notice_history = served_notice_histories.first()
    privacy_notice_history = (
        db.query(PrivacyNoticeHistory)
        .filter(
            PrivacyNoticeHistory.id == served_notice_history.privacy_notice_history_id
        )
        .first()
    )
    db.refresh(privacy_preference_history)

    assert (
        served_notice_history.notice_name
        == privacy_notice_history.name
        == "Data Sales and Sharing"
    )
    assert (
        served_notice_history.notice_key
        == privacy_notice_history.notice_key
        == "data_sales_and_sharing"
    )
    assert (
        served_notice_history.notice_mechanism
        == privacy_notice_history.consent_mechanism
        == ConsentMechanism.opt_out
    )
    assert served_notice_history.served_notice_history_id == served_notice_history.id

    print("> Verified Served Notice History migration.")

    existing_preferences = db.query(DeprecatedCurrentPrivacyPreference)
    migrated_current_preferences = db.query(CurrentPrivacyPreferenceV2).order_by(
        CurrentPrivacyPreferenceV2.created_at.asc()
    )
    assert existing_preferences.count() == 8
    assert migrated_current_preferences.count() == 4

    notice_id, notice_history_id = get_us_ca_notice_and_history_id(db)
    (
        functional_notice_id,
        functional_notice_history_id,
    ) = get_functional_notice_and_history_id(db)
    (
        essential_notice_id,
        essential_notice_history_id,
    ) = get_essential_notice_and_history_id(db)

    janes_record = migrated_current_preferences.first()
    assert janes_record.hashed_phone_number is None
    assert janes_record.phone_number is None
    assert janes_record.hashed_email == ProvidedIdentity.hash_value("jane@example.com")
    assert janes_record.email == "jane@example.com"
    assert janes_record.hashed_fides_user_device == ProvidedIdentity.hash_value(
        "jane119f-20e4-45df-82f7-5eb68a00889f"
    )
    assert janes_record.fides_user_device == "jane119f-20e4-45df-82f7-5eb68a00889f"
    assert janes_record.created_at
    assert janes_record.updated_at
    assert janes_record.preferences == {
        "preferences": [
            {"preference": "opt_out", "privacy_notice_history": notice_history_id},
            {
                "preference": "opt_in",
                "privacy_notice_history": essential_notice_history_id,
            },
        ]
    }

    joes_record = migrated_current_preferences.offset(1).first()
    assert joes_record.hashed_phone_number is None
    assert joes_record.phone_number is None
    assert joes_record.hashed_email is None
    assert joes_record.email is None
    assert joes_record.hashed_fides_user_device == ProvidedIdentity.hash_value(
        "joe1219f-20e4-45df-82f7-5eb68a00889f"
    )
    assert joes_record.fides_user_device == "joe1219f-20e4-45df-82f7-5eb68a00889f"
    assert joes_record.created_at
    assert joes_record.updated_at
    assert joes_record.preferences == {
        "preferences": [
            {
                "preference": "opt_out",
                "privacy_notice_history": essential_notice_history_id,
            }
        ]
    }

    elizabeths_record = migrated_current_preferences.offset(2).first()
    assert elizabeths_record.hashed_phone_number == ProvidedIdentity.hash_value(
        "+6666666666"
    )
    assert elizabeths_record.phone_number == "+6666666666"
    assert elizabeths_record.hashed_email is None
    assert elizabeths_record.email is None
    assert elizabeths_record.hashed_fides_user_device is None
    assert elizabeths_record.fides_user_device is None
    assert elizabeths_record.created_at
    assert elizabeths_record.updated_at
    assert elizabeths_record.preferences == {
        "preferences": [
            {
                "preference": "opt_out",
                "privacy_notice_history": functional_notice_history_id,
            }
        ]
    }

    dawns_record = migrated_current_preferences.offset(3).first()
    assert dawns_record.hashed_phone_number == ProvidedIdentity.hash_value(
        "+15555555555"
    )
    assert dawns_record.phone_number == "+15555555555"
    assert dawns_record.hashed_email == ProvidedIdentity.hash_value("dawn@example.com")
    assert dawns_record.email == "dawn@example.com"
    assert dawns_record.hashed_fides_user_device == ProvidedIdentity.hash_value(
        "dawn219f-20e4-45df-82f7-5eb68a00889f"
    )
    assert (
        dawns_record.fides_user_device == "dawn219f-20e4-45df-82f7-5eb68a00889f"
    )  # This is the most recent fides device
    assert dawns_record.created_at
    assert dawns_record.updated_at
    # Privacy preferences were consolidated. Multiple preferences against notice_history and the latest was retained
    assert dawns_record.preferences == {
        "preferences": [
            {"preference": "opt_out", "privacy_notice_history": notice_history_id},
            {
                "preference": "opt_out",
                "privacy_notice_history": functional_notice_history_id,
            },
            {
                "preference": "opt_in",
                "privacy_notice_history": essential_notice_history_id,
            },
        ]
    }

    print("> Verified Current Privacy Preference V2 migration.")


if __name__ == "__main__":
    print("> Running Privacy Preferences Migration Script...")

    parser = argparse.ArgumentParser(description="Verify Privacy Preferences Migration")
    parser.add_argument(
        "--run_migration",
        dest="reload",
        action="store_const",
        const=True,
        default=False,
        help="whether or not to redo the migrations and reload the objects",
    )

    args = parser.parse_args()
    SessionLocal = get_db_session(CONFIG)
    db = SessionLocal()

    if args.reload:
        reload_objects(db=db)
    else:
        print("> Verifying Data Migration Updates...")

        verify_migration(db=db)

        print("> Data Verification Complete!")
