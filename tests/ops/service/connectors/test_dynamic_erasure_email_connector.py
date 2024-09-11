from unittest import mock

import pytest
from fideslang.models import FidesDatasetReference
from fideslang.validation import FidesKey

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.connectionconfig import AccessLevel, ConnectionTestStatus
from fides.api.schemas.connection_configuration.connection_secrets_dynamic_erasure_email import (
    DynamicErasureEmailSchema,
)
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    AdvancedSettings,
    IdentityTypes,
)
from fides.api.schemas.messaging.messaging import MessagingActionType
from fides.api.service.connectors.base_erasure_email_connector import (
    filter_user_identities_for_connector,
    get_identity_types_for_connector,
    send_single_erasure_email,
)
from fides.api.service.connectors.dynamic_erasure_email_connector import (
    DynamicErasureEmailConnector,
)
from fides.api.service.privacy_request.request_runner_service import (
    get_erasure_email_connection_configs,
)


class TestDynamicErasureEmailConnectorMethods:
    email_defined = DynamicErasureEmailSchema(
        third_party_vendor_name=FidesDatasetReference(
            dataset=FidesKey("test_dataset"), field="collection.vendor"
        ),
        recipient_email_address=FidesDatasetReference(
            dataset=FidesKey("test_dataset"), field="collection.email"
        ),
        advanced_settings=AdvancedSettings(
            identity_types=IdentityTypes(email=True, phone_number=False)
        ),
    )

    phone_defined = DynamicErasureEmailSchema(
        third_party_vendor_name=FidesDatasetReference(
            dataset=FidesKey("test_dataset"), field="collection.vendor"
        ),
        recipient_email_address=FidesDatasetReference(
            dataset=FidesKey("test_dataset"), field="collection.email"
        ),
        advanced_settings=AdvancedSettings(
            identity_types=IdentityTypes(email=False, phone_number=True)
        ),
    )

    email_and_phone_defined = DynamicErasureEmailSchema(
        third_party_vendor_name=FidesDatasetReference(
            dataset=FidesKey("test_dataset"), field="collection.vendor"
        ),
        recipient_email_address=FidesDatasetReference(
            dataset=FidesKey("test_dataset"), field="collection.email"
        ),
        advanced_settings=AdvancedSettings(
            identity_types=IdentityTypes(email=True, phone_number=True)
        ),
    )

    def test_get_erasure_email_connection_configs_none(self, db):
        assert not get_erasure_email_connection_configs(db).first()

    @pytest.mark.parametrize(
        "email_schema, identity_types",
        [
            (email_defined, ["email"]),
            (phone_defined, ["phone_number"]),
            (email_and_phone_defined, ["email", "phone_number"]),
        ],
    )
    def test_get_identity_types_for_connector_both_types_supplied(
        self, email_schema, identity_types
    ):
        assert get_identity_types_for_connector(email_schema) == identity_types

    @pytest.mark.parametrize(
        "email_schema, user_identities, filtered_identities",
        [
            (
                email_defined,
                {"email": "test@example.com"},
                {"email": "test@example.com"},
            ),
            (
                email_defined,
                {"phone_number": "333-222-2221"},
                {},
            ),
            (
                email_defined,
                {"email": "test@example.com", "phone_number": "333-222-2221"},
                {"email": "test@example.com"},
            ),
            (
                phone_defined,
                {"email": "test@example.com"},
                {},
            ),
            (
                phone_defined,
                {"phone_number": "333-222-2221"},
                {"phone_number": "333-222-2221"},
            ),
            (
                phone_defined,
                {"email": "test@example.com", "phone_number": "333-222-2221"},
                {"phone_number": "333-222-2221"},
            ),
            (
                email_and_phone_defined,
                {"email": "test@example.com"},
                {"email": "test@example.com"},
            ),
            (
                email_and_phone_defined,
                {"phone_number": "333-222-2221"},
                {"phone_number": "333-222-2221"},
            ),
            (
                email_and_phone_defined,
                {"email": "test@example.com", "phone_number": "333-222-2221"},
                {"email": "test@example.com", "phone_number": "333-222-2221"},
            ),
        ],
    )
    def test_get_user_identities_for_connector(
        self, email_schema, user_identities, filtered_identities
    ):
        assert (
            filter_user_identities_for_connector(email_schema, user_identities)
            == filtered_identities
        )

    def test_needs_email(
        self,
        test_dynamic_erasure_email_connector,
        privacy_request_with_erasure_policy,
    ):
        assert (
            test_dynamic_erasure_email_connector.needs_email(
                {"email": "test@example.com"},
                privacy_request_with_erasure_policy,
            )
            is True
        )

    def test_needs_email_without_erasure_rules(
        self, test_dynamic_erasure_email_connector, privacy_request
    ):
        assert (
            test_dynamic_erasure_email_connector.needs_email(
                {"email": "test@example.com"},
                privacy_request,
            )
            is False
        )

    def test_needs_email_unsupported_identity(
        self,
        test_dynamic_erasure_email_connector,
        privacy_request_with_erasure_policy,
    ):
        assert (
            test_dynamic_erasure_email_connector.needs_email(
                {"phone": "333-222-2221"},
                privacy_request_with_erasure_policy,
            )
            is False
        )


class TestDynamicErasureEmailConnector:
    def test_dynamic_identities_for_test_email_property(
        self, test_dynamic_erasure_email_connector
    ):
        assert test_dynamic_erasure_email_connector.identities_for_test_email == {
            "email": "test_email@example.com"
        }

    def test_required_identities_property(self, test_dynamic_erasure_email_connector):
        assert test_dynamic_erasure_email_connector.required_identities == ["email"]

    def test_connection_no_test_email_address(
        self, db, test_dynamic_erasure_email_connector
    ):
        # Set test_email_address to None
        connection_config = test_dynamic_erasure_email_connector.configuration
        connection_config.secrets["test_email_address"] = None
        connection_config.save(db=db)

        status = test_dynamic_erasure_email_connector.test_connection()
        assert status == ConnectionTestStatus.failed

    @mock.patch(
        "fides.api.service.connectors.dynamic_erasure_email_connector.send_single_erasure_email"
    )
    def test_test_connection_call(
        self, mock_send_email, db, test_dynamic_erasure_email_connector
    ):
        test_dynamic_erasure_email_connector.test_connection()
        assert mock_send_email.called

        call_kwargs = mock_send_email.call_args.kwargs
        assert call_kwargs["db"] == db
        assert (
            call_kwargs["subject_email"]
            == test_dynamic_erasure_email_connector.configuration.secrets[
                "test_email_address"
            ]
        )
        assert call_kwargs["subject_email"] == "test@example.com"
        assert call_kwargs["subject_name"] == "Test Vendor"
        assert call_kwargs["batch_identities"] == ["test_email@example.com"]
        assert call_kwargs["test_mode"]
