from copy import deepcopy
from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.privacy_preference import (
    ConsentIdentitiesMixin,
    CurrentPrivacyPreference,
    PrivacyPreferenceHistory,
    ServedNoticeHistory,
    ServingComponent,
)
from fides.api.models.privacy_request import (
    Consent,
    ConsentRequest,
    ProvidedIdentity,
)
from fides.api.schemas.privacy_request import PrivacyRequestSource
from fides.api.schemas.redis_cache import CustomPrivacyRequestField
from tests.fixtures.privacy_request_fixtures import _create_privacy_request_for_policy


@pytest.fixture(scope="function")
def empty_provided_identity(db):
    provided_identity = ProvidedIdentity.create(db, data={"field_name": "email"})
    yield provided_identity
    provided_identity.delete(db)


@pytest.fixture(scope="function")
def custom_provided_identity(db):
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "customer_id",
        "field_label": "Customer ID",
        "hashed_value": ProvidedIdentity.hash_value("123"),
        "encrypted_value": {"value": "123"},
    }
    provided_identity = ProvidedIdentity.create(
        db,
        data=provided_identity_data,
    )
    yield provided_identity
    provided_identity.delete(db=db)


@pytest.fixture(scope="function")
def provided_identity_value():
    return "test@email.com"


@pytest.fixture(scope="function")
def provided_identity_and_consent_request(
    db,
    provided_identity_value,
):
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "email",
        "hashed_value": ProvidedIdentity.hash_value(provided_identity_value),
        "encrypted_value": {"value": provided_identity_value},
    }
    provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

    consent_request_data = {
        "provided_identity_id": provided_identity.id,
        "source": PrivacyRequestSource.privacy_center,
    }
    consent_request = ConsentRequest.create(db, data=consent_request_data)

    yield provided_identity, consent_request
    provided_identity.delete(db=db)
    consent_request.delete(db=db)


@pytest.fixture(scope="function")
def provided_identity_and_consent_request_with_custom_fields(
    db,
    provided_identity_and_consent_request,
):
    _, consent_request = provided_identity_and_consent_request
    consent_request.persist_custom_privacy_request_fields(
        db=db,
        custom_privacy_request_fields={
            "first_name": CustomPrivacyRequestField(label="First name", value="John"),
            "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
        },
    )
    return consent_request


@pytest.fixture(scope="function")
def fides_user_provided_identity(db):
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "fides_user_device_id",
        "hashed_value": ProvidedIdentity.hash_value(
            "051b219f-20e4-45df-82f7-5eb68a00889f"
        ),
        "encrypted_value": {"value": "051b219f-20e4-45df-82f7-5eb68a00889f"},
    }
    provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

    yield provided_identity
    provided_identity.delete(db=db)


@pytest.fixture(scope="function")
def fides_user_provided_identity_and_consent_request(db, fides_user_provided_identity):
    consent_request_data = {
        "provided_identity_id": fides_user_provided_identity.id,
    }
    consent_request = ConsentRequest.create(db, data=consent_request_data)

    yield fides_user_provided_identity, consent_request
    fides_user_provided_identity.delete(db=db)
    consent_request.delete(db=db)


@pytest.fixture(scope="function")
def executable_consent_request(
    db,
    provided_identity_and_consent_request,
    consent_policy,
):
    provided_identity = provided_identity_and_consent_request[0]
    consent_request = provided_identity_and_consent_request[1]
    privacy_request = _create_privacy_request_for_policy(
        db,
        consent_policy,
    )
    consent_request.privacy_request_id = privacy_request.id
    consent_request.save(db)
    provided_identity.privacy_request_id = privacy_request.id
    provided_identity.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def current_privacy_preference(
    db,
    privacy_notice,
    privacy_experience_privacy_center,
    served_notice_history,
):
    pref = CurrentPrivacyPreference.create(
        db=db,
        data={
            "email": "test@email.com",
            "hashed_email": ConsentIdentitiesMixin.hash_value("test@email.com"),
            "preferences": {
                "purpose_consent_preferences": [],
                "purpose_legitimate_interests_preferences": [],
                "vendor_consent_preferences": [],
                "vendor_legitimate_interests_preferences": [],
                "special_feature_preferences": [],
                "preferences": [
                    {
                        "privacy_notice_history_id": privacy_notice.histories[0].id,
                        "preference": "opt_out",
                    }
                ],
                "special_purpose_preferences": [],
                "feature_preferences": [],
                "system_consent_preferences": [],
                "system_legitimate_interests_preferences": [],
            },
        },
    )

    yield pref

    pref.delete(db)


@pytest.fixture(scope="function")
def privacy_preference_history(
    db,
    privacy_notice,
    privacy_experience_privacy_center,
    served_notice_history,
):
    privacy_notice_history = privacy_notice.translations[0].histories[0]

    preference_history_record = PrivacyPreferenceHistory.create(
        db=db,
        data={
            "anonymized_ip_address": "92.158.1.0",
            "email": "test@email.com",
            "method": "button",
            "privacy_experience_config_history_id": privacy_experience_privacy_center.experience_config.translations[
                0
            ].privacy_experience_config_history_id,
            "preference": "opt_out",
            "privacy_notice_history_id": privacy_notice_history.id,
            "request_origin": "privacy_center",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
            "user_geography": "us_ca",
            "url_recorded": "https://example.com/privacy_center",
            "served_notice_history_id": served_notice_history.served_notice_history_id,
        },
        check_name=False,
    )
    yield preference_history_record
    preference_history_record.delete(db)


@pytest.fixture(scope="function")
def privacy_preference_history_us_ca_provide(
    db: Session,
    privacy_notice_us_ca_provide,
    privacy_preference_history,
    privacy_experience_privacy_center,
    served_notice_history,
) -> Generator:
    preference_history_record = PrivacyPreferenceHistory.create(
        db=db,
        data={
            "anonymized_ip_address": "92.158.1.0",
            "email": "test@email.com",
            "method": "button",
            "privacy_experience_config_history_id": privacy_experience_privacy_center.experience_config.translations[
                0
            ].privacy_experience_config_history_id,
            "preference": "opt_in",
            "privacy_notice_history_id": privacy_notice_us_ca_provide.translations[
                0
            ].privacy_notice_history_id,
            "request_origin": "privacy_center",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
            "user_geography": "us_ca",
            "url_recorded": "https://example.com/privacy_center",
            "served_notice_history_id": served_notice_history.served_notice_history_id,
        },
        check_name=False,
    )

    yield preference_history_record
    preference_history_record.delete(db)


@pytest.fixture(scope="function")
def privacy_preference_history_fr_provide_service_frontend_only(
    db: Session,
    privacy_notice_fr_provide_service_frontend_only,
    privacy_experience_privacy_center,
    served_notice_history,
) -> Generator:
    preference_history_record = PrivacyPreferenceHistory.create(
        db=db,
        data={
            "anonymized_ip_address": "92.158.1.0",
            "email": "test@email.com",
            "method": "button",
            "privacy_experience_config_history_id": privacy_experience_privacy_center.experience_config.translations[
                0
            ].privacy_experience_config_history_id,
            "preference": "opt_out",
            "privacy_notice_history_id": privacy_notice_fr_provide_service_frontend_only.translations[
                0
            ].privacy_notice_history_id,
            "request_origin": "privacy_center",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
            "user_geography": "fr_idg",
            "url_recorded": "https://example.com/privacy_center",
            "served_notice_history_id": served_notice_history.served_notice_history_id,
        },
        check_name=False,
    )

    yield preference_history_record
    preference_history_record.delete(db)


@pytest.fixture(scope="function")
def anonymous_consent_records(
    db,
    fides_user_provided_identity_and_consent_request,
):
    (
        provided_identity,
        consent_request,
    ) = fides_user_provided_identity_and_consent_request
    consent_request.cache_identity_verification_code("abcdefg")

    consent_data = [
        {
            "data_use": "email",
            "data_use_description": None,
            "opt_in": True,
        },
        {
            "data_use": "location",
            "data_use_description": "Location data",
            "opt_in": False,
        },
    ]

    records = []
    for data in deepcopy(consent_data):
        data["provided_identity_id"] = provided_identity.id
        records.append(Consent.create(db, data=data))

    yield records

    for record in records:
        record.delete(db)


@pytest.fixture(scope="function")
def consent_records(
    db,
    provided_identity_and_consent_request,
):
    provided_identity, consent_request = provided_identity_and_consent_request
    consent_request.cache_identity_verification_code("abcdefg")

    consent_data = [
        {
            "data_use": "email",
            "data_use_description": None,
            "opt_in": True,
        },
        {
            "data_use": "location",
            "data_use_description": "Location data",
            "opt_in": False,
        },
    ]

    records = []
    for data in deepcopy(consent_data):
        data["provided_identity_id"] = provided_identity.id
        records.append(Consent.create(db, data=data))

    yield records

    for record in records:
        record.delete(db)


# TODO: This was a duplicate of the served_notice_history fixture.
@pytest.fixture(scope="function")
def served_notice_history(
    db: Session, privacy_notice, fides_user_provided_identity
) -> Generator:
    pref_1 = ServedNoticeHistory.create(
        db=db,
        data={
            "acknowledge_mode": False,
            "serving_component": ServingComponent.overlay,
            "privacy_notice_history_id": privacy_notice.translations[
                0
            ].privacy_notice_history_id,
            "email": "test@example.com",
            "hashed_email": ConsentIdentitiesMixin.hash_value("test@example.com"),
            "served_notice_history_id": "ser_12345",
        },
        check_name=False,
    )
    yield pref_1
    pref_1.delete(db)
