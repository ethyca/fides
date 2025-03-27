import pytest

from fides.api.models.privacy_request import ProvidedIdentity
from fides.api.models.privacy_request.consent import Consent, ConsentRequest
from fides.api.schemas.privacy_request import CustomPrivacyRequestField


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


class TestConsentRequestCustomFieldFunctions:
    """Similar to the above tests but for the ConsentRequest model but only testing persisting and retrieving from the database."""

    @pytest.fixture(scope="function")
    def consent_request(self, db) -> ConsentRequest:
        provided_identity_data = {
            "privacy_request_id": None,
            "field_name": "email",
            "encrypted_value": {"value": "test@email.com"},
        }
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

        consent_request = ConsentRequest.create(
            db=db,
            data={
                "provided_identity_id": provided_identity.id,
            },
        )

        yield consent_request

        consent_request.delete(db)

    def test_persist_custom_privacy_request_fields(
        self,
        db,
        consent_request,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_fields_in_request_execution_enabled,
    ):
        consent_request.persist_custom_privacy_request_fields(
            db=db,
            custom_privacy_request_fields={
                "first_name": CustomPrivacyRequestField(
                    label="First name", value="John"
                ),
                "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
                "subscriber_ids": CustomPrivacyRequestField(
                    label="Subscriber IDs", value=["123", "456"]
                ),
                "account_ids": CustomPrivacyRequestField(
                    label="Account IDs", value=[123, 456]
                ),
            },
        )
        assert consent_request.get_persisted_custom_privacy_request_fields() == {
            "first_name": {"label": "First name", "value": "John"},
            "last_name": {"label": "Last name", "value": "Doe"},
            "subscriber_ids": {"label": "Subscriber IDs", "value": ["123", "456"]},
            "account_ids": {"label": "Account IDs", "value": [123, 456]},
        }

    def test_persist_custom_privacy_request_fields_collection_disabled(
        self,
        db,
        consent_request,
        allow_custom_privacy_request_field_collection_disabled,
    ):
        """Custom privacy request fields should not be persisted if collection is disabled"""
        consent_request.persist_custom_privacy_request_fields(
            db=db,
            custom_privacy_request_fields={
                "first_name": CustomPrivacyRequestField(
                    label="First name", value="John"
                ),
                "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
                "subscriber_ids": CustomPrivacyRequestField(
                    label="Subscriber IDs", value=["123", "456"]
                ),
                "account_ids": CustomPrivacyRequestField(
                    label="Account IDs", value=[123, 456]
                ),
            },
        )
        assert consent_request.get_persisted_custom_privacy_request_fields() == {}


def test_verify_identity(db, provided_identity_and_consent_request):
    _, consent_request = provided_identity_and_consent_request

    assert consent_request.identity_verified_at is None

    consent_request.cache_identity_verification_code("abcdefg")
    consent_request.verify_identity(db, provided_code="abcdefg")

    assert consent_request.identity_verified_at is not None

    with pytest.raises(PermissionError):
        consent_request.verify_identity(db, provided_code="wrongcode")
