import pytest
from pydantic import ValidationError

from fides.api.schemas.redis_cache import Identity


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

    def test_none_custom_identity(self):
        with pytest.raises(ValidationError) as exc:
            Identity(
                customer_id={"label": "Customer ID", "value": None},
            )
        assert "3 validation errors for LabeledIdentity" in str(exc.value)

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
