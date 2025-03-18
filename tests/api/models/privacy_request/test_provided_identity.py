import pytest

from fides.api.models.privacy_request.provided_identity import (
    ProvidedIdentity,
    ProvidedIdentityType,
)
from fides.api.schemas.redis_cache import Identity


@pytest.fixture
def provided_identity_data():
    provided_identity_value = "test_email@ethyca.com"
    return {
        "field_name": "email",
        "hashed_value": ProvidedIdentity.hash_value(provided_identity_value),
        "encrypted_value": {"value": provided_identity_value},
    }


def test_create_provided_identity(db, provided_identity_data, privacy_request):
    # Test with privacy_request_id as None and as a valid privacy_request_id
    for privacy_request_id in [None, privacy_request.id]:
        provided_identity_data["privacy_request_id"] = privacy_request_id
        provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

        # Query the ProvidedIdentity
        retrieved_identity = (
            db.query(ProvidedIdentity)
            .filter_by(hashed_value=provided_identity_data["hashed_value"])
            .first()
        )
        assert retrieved_identity is not None
        assert retrieved_identity.field_name == "email"
        assert retrieved_identity.privacy_request_id == privacy_request_id

        provided_identity.delete(db)


@pytest.mark.parametrize(
    "hash_function",
    [
        ProvidedIdentity.bcrypt_hash_value,
        ProvidedIdentity.hash_value,
    ],
    ids=["bcrypt_hash_value", "hash_value"],
)
def test_hash_value_basic(hash_function):
    value = "test_value"
    hashed_value = hash_function(value)

    assert hashed_value is not None
    assert isinstance(hashed_value, str)
    assert hashed_value != value  # Ensure the hash is different from the input


@pytest.mark.parametrize(
    "hash_function",
    [
        ProvidedIdentity.bcrypt_hash_value,
        ProvidedIdentity.hash_value,
    ],
    ids=["bcrypt_hash_value", "hash_value"],
)
def test_hash_value_deterministic(hash_function):
    value = "test_value"
    hashed_value_1 = hash_function(value)
    hashed_value_2 = hash_function(value)

    # If the function is deterministic, the hashes should match
    assert hashed_value_1 == hashed_value_2


@pytest.mark.parametrize(
    "hash_function",
    [
        ProvidedIdentity.bcrypt_hash_value,
        ProvidedIdentity.hash_value,
    ],
    ids=["bcrypt_hash_value", "hash_value"],
)
def test_hash_value_different_inputs(hash_function):
    value_1 = "test_value_1"
    value_2 = "test_value_2"

    hashed_value_1 = hash_function(value_1)
    hashed_value_2 = hash_function(value_2)

    # Ensure different inputs produce different hashes
    assert hashed_value_1 != hashed_value_2


@pytest.mark.parametrize(
    "hash_function",
    [
        ProvidedIdentity.bcrypt_hash_value,
        ProvidedIdentity.hash_value,
    ],
    ids=["bcrypt_hash_value", "hash_value"],
)
def test_hash_value_empty_string(hash_function):
    value = ""
    hashed_value = hash_function(value)

    assert hashed_value is not None
    assert isinstance(hashed_value, str)


@pytest.mark.parametrize(
    "hash_function",
    [
        ProvidedIdentity.bcrypt_hash_value,
        ProvidedIdentity.hash_value,
    ],
    ids=["bcrypt_hash_value", "hash_value"],
)
def test_hash_value_large_input(hash_function):
    value = "a" * 10000  # Very large input
    hashed_value = hash_function(value)

    assert hashed_value is not None
    assert isinstance(hashed_value, str)


def test_migrate_hashed_fields(db, provided_identity_data):
    provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)
    provided_identity.migrate_hashed_fields()
    assert provided_identity.is_hash_migrated
    provided_identity.delete(db)


def test_as_identity_schema_basic(db, provided_identity_data):
    provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

    # Call the as_identity_schema method
    identity_schema = provided_identity.as_identity_schema()

    assert isinstance(identity_schema, Identity)
    assert identity_schema.phone_number is None
    assert identity_schema.email == "test_email@ethyca.com"
    assert identity_schema.ga_client_id is None
    assert identity_schema.ljt_readerID is None
    assert identity_schema.fides_user_device_id is None
    assert identity_schema.external_id is None

    provided_identity.delete(db)


def test_as_identity_schema_missing_encrypted_value(db, provided_identity_data):
    provided_identity_data.pop("encrypted_value")
    provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

    # Call the as_identity_schema method
    identity_schema = provided_identity.as_identity_schema()

    assert isinstance(identity_schema, Identity)
    assert identity_schema.phone_number is None
    assert identity_schema.email is None
    assert identity_schema.ga_client_id is None
    assert identity_schema.ljt_readerID is None
    assert identity_schema.fides_user_device_id is None
    assert identity_schema.external_id is None

    provided_identity.delete(db)
