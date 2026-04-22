import pytest
from pydantic import ValidationError

from fides.api.schemas.redis_cache import (
    CustomPrivacyRequestField,
    Identity,
    UnverifiedIdentity,
)


class TestIdentitySchema:
    def test_email_identity(self):
        Identity(email="user@example.com")

    def test_valid_custom_identity(self):
        Identity(customer_id={"label": "Customer ID", "value": "123"})

    def test_mixed_identities(self):
        Identity(
            email="user@example.com",
            customer_id={"label": "Customer ID", "value": "123"},
        )

    def test_multiple_custom_identities(self):
        Identity(
            customer_id={"label": "Customer ID", "value": "123"},
            account_id={"label": "Account ID", "value": 123},
        )

    @pytest.mark.parametrize("bool_value", [True, False])
    def test_bool_custom_identity_preserves_type(self, bool_value):
        """bool values must round-trip as bool, not be coerced to int.

        Pins the `StrictBool` ordering in the MultiValue union in
        `redis_cache.py` — Python treats bool as a subclass of int, so if
        StrictInt precedes StrictBool the bool value would be accepted there
        and its type would be silently lost.
        """
        identity = Identity(
            opted_in={"label": "Opted In", "value": bool_value},
        )
        assert identity.opted_in.value is bool_value
        assert type(identity.opted_in.value) is bool

    def test_bool_custom_identity_round_trip(self):
        """bool value survives a full dump -> reload cycle without coercion."""
        original = Identity(
            opted_in={"label": "Opted In", "value": True},
        )
        reloaded = Identity(opted_in=original.labeled_dict()["opted_in"])
        assert reloaded.opted_in.value is True
        assert type(reloaded.opted_in.value) is bool

    def test_none_custom_identity(self):
        with pytest.raises(ValidationError) as exc:
            Identity(
                customer_id={"label": "Customer ID", "value": None},
            )
        # Every branch of the MultiValue union rejects None; assert on the
        # failing field rather than the error count (which shifts with union size).
        errors = exc.value.errors()
        assert all(err["loc"][0] == "value" for err in errors)

    def test_invalid_custom_identity(self):
        with pytest.raises(ValueError) as exc:
            Identity(customer_id="123")
        assert (
            str(exc.value)
            == 'Custom identity "customer_id" must be an instance of LabeledIdentity (e.g. {"label": "Field label", "value": "123"})'
        )

    @pytest.mark.parametrize(
        "identity_data, expected_dict",
        [
            (
                {
                    "email": "user@example.com",
                },
                {
                    "phone_number": None,
                    "email": "user@example.com",
                    "ga_client_id": None,
                    "ljt_readerID": None,
                    "fides_user_device_id": None,
                    "external_id": None,
                },
            ),
            (
                {
                    "customer_id": {"label": "Customer ID", "value": "123"},
                },
                {
                    "phone_number": None,
                    "email": None,
                    "ga_client_id": None,
                    "ljt_readerID": None,
                    "fides_user_device_id": None,
                    "external_id": None,
                    "customer_id": "123",
                },
            ),
            (
                {
                    "email": "user@example.com",
                    "customer_id": {"label": "Customer ID", "value": "123"},
                },
                {
                    "phone_number": None,
                    "email": "user@example.com",
                    "ga_client_id": None,
                    "ljt_readerID": None,
                    "fides_user_device_id": None,
                    "external_id": None,
                    "customer_id": "123",
                },
            ),
            (
                {
                    "email": "user@example.com",
                    "phone_number": "+15558675309",
                    "ga_client_id": "GA123",
                    "ljt_readerID": "LJT456",
                    "fides_user_device_id": "4fbb6edf-34f6-4717-a6f1-541fd1e5d585",
                    "external_id": "ext-123",
                },
                {
                    "phone_number": "+15558675309",
                    "email": "user@example.com",
                    "ga_client_id": "GA123",
                    "ljt_readerID": "LJT456",
                    "fides_user_device_id": "4fbb6edf-34f6-4717-a6f1-541fd1e5d585",
                    "external_id": "ext-123",
                },
            ),
        ],
    )
    def test_identity_dict(self, identity_data, expected_dict):
        identity = Identity(**identity_data)
        assert identity.model_dump(mode="json") == expected_dict

    @pytest.mark.parametrize(
        "identity_data, expected_dict",
        [
            (
                {
                    "email": "user@example.com",
                },
                {
                    "phone_number": None,
                    "email": "user@example.com",
                    "ga_client_id": None,
                    "ljt_readerID": None,
                    "fides_user_device_id": None,
                    "external_id": None,
                },
            ),
            (
                {
                    "customer_id": {"label": "Customer ID", "value": "123"},
                },
                {
                    "phone_number": None,
                    "email": None,
                    "ga_client_id": None,
                    "ljt_readerID": None,
                    "fides_user_device_id": None,
                    "external_id": None,
                    "customer_id": {"label": "Customer ID", "value": "123"},
                },
            ),
            (
                {
                    "email": "user@example.com",
                    "customer_id": {"label": "Customer ID", "value": "123"},
                },
                {
                    "phone_number": None,
                    "email": "user@example.com",
                    "ga_client_id": None,
                    "ljt_readerID": None,
                    "fides_user_device_id": None,
                    "external_id": None,
                    "customer_id": {"label": "Customer ID", "value": "123"},
                },
            ),
            (
                {
                    "email": "user@example.com",
                    "phone_number": "+15558675309",
                    "ga_client_id": "GA123",
                    "ljt_readerID": "LJT456",
                    "fides_user_device_id": "4fbb6edf-34f6-4717-a6f1-541fd1e5d585",
                    "external_id": "ext-123",
                },
                {
                    "phone_number": "+15558675309",
                    "email": "user@example.com",
                    "ga_client_id": "GA123",
                    "ljt_readerID": "LJT456",
                    "fides_user_device_id": "4fbb6edf-34f6-4717-a6f1-541fd1e5d585",
                    "external_id": "ext-123",
                },
            ),
        ],
    )
    def test_identity_labeled_dict(self, identity_data, expected_dict):
        identity = Identity(**identity_data)
        assert identity.labeled_dict() == expected_dict

    @pytest.mark.parametrize(
        "identity_data, expected_dict",
        [
            (
                {
                    "email": "user@example.com",
                },
                {
                    "phone_number": {"label": "Phone number", "value": None},
                    "email": {"label": "Email", "value": "user@example.com"},
                    "ga_client_id": {"label": "GA client ID", "value": None},
                    "ljt_readerID": {"label": "LJT reader ID", "value": None},
                    "fides_user_device_id": {
                        "label": "Fides user device ID",
                        "value": None,
                    },
                    "external_id": {"label": "External ID", "value": None},
                },
            ),
            (
                {
                    "customer_id": {"label": "Customer ID", "value": "123"},
                },
                {
                    "phone_number": {"label": "Phone number", "value": None},
                    "email": {"label": "Email", "value": None},
                    "ga_client_id": {"label": "GA client ID", "value": None},
                    "ljt_readerID": {"label": "LJT reader ID", "value": None},
                    "fides_user_device_id": {
                        "label": "Fides user device ID",
                        "value": None,
                    },
                    "external_id": {"label": "External ID", "value": None},
                    "customer_id": {"label": "Customer ID", "value": "123"},
                },
            ),
            (
                {
                    "email": "user@example.com",
                    "customer_id": {"label": "Customer ID", "value": "123"},
                },
                {
                    "phone_number": {"label": "Phone number", "value": None},
                    "email": {"label": "Email", "value": "user@example.com"},
                    "ga_client_id": {"label": "GA client ID", "value": None},
                    "ljt_readerID": {"label": "LJT reader ID", "value": None},
                    "fides_user_device_id": {
                        "label": "Fides user device ID",
                        "value": None,
                    },
                    "external_id": {"label": "External ID", "value": None},
                    "customer_id": {"label": "Customer ID", "value": "123"},
                },
            ),
            (
                {
                    "email": "user@example.com",
                    "phone_number": "+15558675309",
                    "ga_client_id": "GA123",
                    "ljt_readerID": "LJT456",
                    "fides_user_device_id": "4fbb6edf-34f6-4717-a6f1-541fd1e5d585",
                    "external_id": "ext-123",
                },
                {
                    "phone_number": {"label": "Phone number", "value": "+15558675309"},
                    "email": {"label": "Email", "value": "user@example.com"},
                    "ga_client_id": {"label": "GA client ID", "value": "GA123"},
                    "ljt_readerID": {"label": "LJT reader ID", "value": "LJT456"},
                    "fides_user_device_id": {
                        "label": "Fides user device ID",
                        "value": "4fbb6edf-34f6-4717-a6f1-541fd1e5d585",
                    },
                    "external_id": {"label": "External ID", "value": "ext-123"},
                },
            ),
        ],
    )
    def test_identity_labeled_dict_include_default_labels(
        self, identity_data, expected_dict
    ):
        identity = Identity(**identity_data)
        assert identity.labeled_dict(include_default_labels=True) == expected_dict


class TestUnverifiedIdentitySchema:
    def test_error_email_identity(self):
        with pytest.raises(ValueError) as exc:
            UnverifiedIdentity(email="user@example.com")
        assert 'Identity "email" not allowed' in str(exc.value)

    def test_error_phone_number_identity(self):
        with pytest.raises(ValueError) as exc:
            UnverifiedIdentity(phone_number="+15558675309")
        assert 'Identity "phone_number" not allowed' in str(exc.value)

    def test_valid_custom_identity(self):
        UnverifiedIdentity(customer_id={"label": "Customer ID", "value": "123"})

    def test_invalid_custom_identity(self):
        with pytest.raises(ValueError) as exc:
            UnverifiedIdentity(customer_id="123")
        assert (
            str(exc.value)
            == 'Custom identity "customer_id" must be an instance of LabeledIdentity (e.g. {"label": "Field label", "value": "123"})'
        )


class TestCustomPrivacyRequestFieldSchema:
    """Schema used for caching/persisting custom privacy center fields."""

    @pytest.mark.parametrize("bool_value", [True, False])
    def test_bool_value_preserved(self, bool_value):
        field = CustomPrivacyRequestField(label="Agree", value=bool_value)
        assert field.value is bool_value
        assert type(field.value) is bool

    def test_list_of_mixed_primitives(self):
        field = CustomPrivacyRequestField(label="Reasons", value=["A", "B", 1, True])
        assert field.value == ["A", "B", 1, True]
        assert type(field.value[3]) is bool

    def test_textarea_long_string(self):
        long_text = "lorem ipsum " * 100
        field = CustomPrivacyRequestField(label="Notes", value=long_text)
        assert field.value == long_text
