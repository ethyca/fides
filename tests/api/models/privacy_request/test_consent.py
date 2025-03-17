from unittest.mock import MagicMock

import pytest

from fides.api.models.privacy_request.consent import Consent, ConsentRequest
from fides.api.schemas.redis_cache import (
    CustomPrivacyRequestField as CustomPrivacyRequestFieldSchema,
)
from fides.config import CONFIG


@pytest.fixture
def mock_db_session():
    return MagicMock()


@pytest.mark.parametrize(
    "identity_fixture",
    [
        pytest.param("fides_user_provided_identity", id="fides_user_identity"),
        pytest.param("empty_provided_identity", id="empty_identity"),
        pytest.param("custom_provided_identity", id="custom_identity"),
    ],
)
def test_create_consent(db, request, identity_fixture):
    identity = request.getfixturevalue(identity_fixture)
    data = {
        "provided_identity_id": identity.id,
        "data_use": "functional.storage",
        "data_use_description": "test_description",
        "opt_in": True,
    }

    Consent.create(db, data=data)

    retrieved_consent = (
        db.query(Consent).filter_by(provided_identity_id=identity.id).first()
    )
    assert retrieved_consent is not None
    assert retrieved_consent.data_use == "functional.storage"
    assert retrieved_consent.data_use_description == "test_description"
    assert retrieved_consent.opt_in is True
    assert retrieved_consent.provided_identity == identity


def test_create_consent_violates_unique_constraint(db, fides_user_provided_identity):
    consent = Consent(
        provided_identity_id=fides_user_provided_identity.id,
        data_use="functional.storage",
        data_use_description="test_description",
        opt_in=True,
    )
    db.add(consent)
    db.commit()

    duplicate_consent = Consent(
        provided_identity_id=fides_user_provided_identity.id,
        data_use="functional.storage",
        data_use_description="test_description",
        opt_in=True,
    )
    db.add(duplicate_consent)
    with pytest.raises(Exception):
        db.commit()


@pytest.mark.parametrize(
    "identity_fixture",
    [
        pytest.param("fides_user_provided_identity", id="fides_user_identity"),
        pytest.param("empty_provided_identity", id="empty_identity"),
        pytest.param("custom_provided_identity", id="custom_identity"),
    ],
)
def test_create_consent_request(db, request, identity_fixture):
    identity = request.getfixturevalue(identity_fixture)
    data = {
        "provided_identity_id": identity.id,
        "property_id": "test_property_id",
    }
    consent_request = ConsentRequest.create(db, data=data)

    retrieved_consent_request = (
        db.query(ConsentRequest).filter_by(provided_identity_id=identity.id).first()
    )
    assert retrieved_consent_request is not None
    assert retrieved_consent_request.property_id == "test_property_id"
    assert retrieved_consent_request.provided_identity_id == identity.id
    assert retrieved_consent_request.provided_identity == identity
    assert retrieved_consent_request.custom_fields == []
    assert retrieved_consent_request.preferences is None
    assert retrieved_consent_request.identity_verified_at is None
    assert retrieved_consent_request.source == None
    assert retrieved_consent_request.privacy_request_id is None
    assert retrieved_consent_request.privacy_request is None

    assert consent_request.get_cached_identity_data() == {}


def test_persist_custom_privacy_request_fields_no_fields(
    provided_identity_and_consent_request, mock_db_session
):
    _, consent_request = provided_identity_and_consent_request
    consent_request.persist_custom_privacy_request_fields(mock_db_session, None)
    # Ensure no database operations were performed
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()


def test_persist_custom_privacy_request_fields_disabled(
    provided_identity_and_consent_request_with_custom_fields, mock_db_session
):
    consent_request = provided_identity_and_consent_request_with_custom_fields
    CONFIG.execution.allow_custom_privacy_request_field_collection = False
    custom_fields = {
        "field1": CustomPrivacyRequestFieldSchema(value="value1", label="Field 1"),
    }
    consent_request.persist_custom_privacy_request_fields(
        mock_db_session, custom_fields
    )
    # Ensure no database operations were performed
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()


def test_persist_custom_privacy_request_fields_enabled(
    provided_identity_and_consent_request_with_custom_fields, mock_db_session, mocker
):
    consent_request = provided_identity_and_consent_request_with_custom_fields
    CONFIG.execution.allow_custom_privacy_request_field_collection = True
    custom_fields = {
        "field1": CustomPrivacyRequestFieldSchema(value="value1", label="Field 1"),
    }
    mock_create = mocker.patch(
        "fides.api.models.privacy_request.consent.CustomPrivacyRequestField.create"
    )
    mock_hash_value = mocker.patch(
        "fides.api.models.privacy_request.consent.CustomPrivacyRequestField.hash_value",
        return_value="hashed_value1",
    )

    consent_request.persist_custom_privacy_request_fields(
        mock_db_session, custom_fields
    )

    mock_hash_value.assert_called_once_with("value1")
    mock_create.assert_called_once_with(
        db=mock_db_session,
        data={
            "consent_request_id": consent_request.id,
            "field_name": "field1",
            "field_label": "Field 1",
            "encrypted_value": {"value": "value1"},
            "hashed_value": "hashed_value1",
        },
    )


def test_verify_identity(db, provided_identity_and_consent_request):
    _, consent_request = provided_identity_and_consent_request

    assert consent_request.identity_verified_at is None

    consent_request.cache_identity_verification_code("abcdefg")
    consent_request.verify_identity(db, provided_code="abcdefg")

    assert consent_request.identity_verified_at is not None

    with pytest.raises(PermissionError):
        consent_request.verify_identity(db, provided_code="wrongcode")
