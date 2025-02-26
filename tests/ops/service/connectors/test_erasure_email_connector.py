from unittest import mock

import pytest

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.connectionconfig import AccessLevel, ConnectionTestStatus
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    AdvancedSettings,
    EmailSchema,
    IdentityTypes,
)
from fides.api.schemas.messaging.messaging import MessagingActionType
from fides.api.service.connectors.base_erasure_email_connector import (
    filter_user_identities_for_connector,
    get_identity_types_for_connector,
    send_single_erasure_email,
)
from fides.api.service.connectors.erasure_email_connector import (
    GenericErasureEmailConnector,
)
from fides.api.service.privacy_request.request_runner_service import (
    get_erasure_email_connection_configs,
)


class TestErasureEmailConnectorMethods:
    email_defined = EmailSchema(
        third_party_vendor_name="Dawn's Bookstore",
        recipient_email_address="test@example.com",
        advanced_settings=AdvancedSettings(
            identity_types=IdentityTypes(email=True, phone_number=False)
        ),
    )

    phone_defined = EmailSchema(
        third_party_vendor_name="Dawn's Bookstore",
        recipient_email_address="test@example.com",
        advanced_settings=AdvancedSettings(
            identity_types=IdentityTypes(email=False, phone_number=True)
        ),
    )

    email_and_phone_defined = EmailSchema(
        third_party_vendor_name="Dawn's Bookstore",
        recipient_email_address="test@example.com",
        advanced_settings=AdvancedSettings(
            identity_types=IdentityTypes(email=True, phone_number=True)
        ),
    )

    def test_get_erasure_email_connection_configs_none(self, db):
        assert not get_erasure_email_connection_configs(db).first()

    def test_get_erasure_email_connection_configs(
        self, db, attentive_email_connection_config
    ):
        assert get_erasure_email_connection_configs(db).count() == 1
        assert (
            get_erasure_email_connection_configs(db).first().name
            == attentive_email_connection_config.name
        )

        attentive_email_connection_config.disabled = True
        attentive_email_connection_config.save(db=db)
        assert not get_erasure_email_connection_configs(db).first()

    def test_get_erasure_email_connection_configs_read_only(
        self, db, sovrn_email_connection_config
    ):
        sovrn_email_connection_config.access = AccessLevel.read
        sovrn_email_connection_config.save(db=db)
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

    @mock.patch(
        "fides.api.service.connectors.base_erasure_email_connector.dispatch_message"
    )
    def test_send_single_erasure_email_no_org_defined(self, mock_dispatch, db):
        with pytest.raises(MessageDispatchException) as exc:
            send_single_erasure_email(
                db=db,
                subject_email="attentive@example.com",
                subject_name="To whom it may concern",
                batch_identities=["test@example.com"],
                test_mode=True,
            )

        assert not mock_dispatch.called
        assert (
            exc.value.message
            == "Cannot send an email to third-party vendor. No organization name found."
        )

    @mock.patch(
        "fides.api.service.connectors.base_erasure_email_connector.dispatch_message"
    )
    def test_send_single_erasure_email(
        self, mock_dispatch, test_fides_org, db, messaging_config
    ):
        send_single_erasure_email(
            db=db,
            subject_email="test@example.com",
            subject_name="To whom it may concern",
            batch_identities=["customer-1@example.com"],
            test_mode=True,
        )

        assert mock_dispatch.called
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["db"] == db
        assert (
            call_kwargs["action_type"]
            == MessagingActionType.MESSAGE_ERASURE_REQUEST_FULFILLMENT
        )
        assert call_kwargs["to_identity"].email == "test@example.com"
        assert call_kwargs["to_identity"].phone_number is None
        assert call_kwargs["to_identity"].ga_client_id is None

        assert call_kwargs["service_type"] == "mailgun"
        message_body_params = call_kwargs["message_body_params"]

        assert message_body_params.controller == "Test Org"
        assert message_body_params.third_party_vendor_name == "To whom it may concern"
        assert message_body_params.identities == ["customer-1@example.com"]

        assert (
            call_kwargs["subject_override"]
            == "Test notification of user erasure requests from Test Org"
        )

    @mock.patch(
        "fides.api.service.connectors.base_erasure_email_connector.dispatch_message"
    )
    @pytest.mark.usefixtures(
        "test_fides_org",
        "messaging_config",
        "set_notification_service_type_to_twilio_email",
    )
    def test_send_single_erasure_email_respects_messaging_service_type(
        self,
        mock_dispatch,
        db,
    ):
        """Ensure `notifications.notification_service_type` property is respected in dispatching erasure emails"""
        send_single_erasure_email(
            db=db,
            subject_email="test@example.com",
            subject_name="To whom it may concern",
            batch_identities=["customer-1@example.com"],
            test_mode=True,
        )

        assert mock_dispatch.called
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["service_type"] == "twilio_email"

    def test_needs_email(
        self,
        test_attentive_erasure_email_connector,
        privacy_request_with_erasure_policy,
    ):
        assert (
            test_attentive_erasure_email_connector.needs_email(
                {"email": "test@example.com"},
                privacy_request_with_erasure_policy,
            )
            is True
        )

    def test_needs_email_without_erasure_rules(
        self, test_attentive_erasure_email_connector, privacy_request
    ):
        assert (
            test_attentive_erasure_email_connector.needs_email(
                {"email": "test@example.com"},
                privacy_request,
            )
            is False
        )

    def test_needs_email_unsupported_identity(
        self,
        test_attentive_erasure_email_connector,
        privacy_request_with_erasure_policy,
    ):
        assert (
            test_attentive_erasure_email_connector.needs_email(
                {"phone": "333-222-2221"},
                privacy_request_with_erasure_policy,
            )
            is False
        )


class TestAttentiveConnector:
    def test_generic_identities_for_test_email_property(
        self, attentive_email_connection_config
    ):
        generic_connector = GenericErasureEmailConnector(
            attentive_email_connection_config
        )
        assert generic_connector.identities_for_test_email == {
            "email": "test_email@example.com"
        }

    def test_attentive_identities_for_test_email_property(
        self, test_attentive_erasure_email_connector
    ):
        assert test_attentive_erasure_email_connector.identities_for_test_email == {
            "email": "test_email@example.com"
        }

    def test_required_identities_property(self, test_attentive_erasure_email_connector):
        assert test_attentive_erasure_email_connector.required_identities == ["email"]

    def test_connection_no_test_email_address(
        self, db, test_attentive_erasure_email_connector
    ):
        # Set test_email_address to None
        connection_config = test_attentive_erasure_email_connector.configuration
        connection_config.secrets["test_email_address"] = None
        connection_config.save(db=db)

        status = test_attentive_erasure_email_connector.test_connection()
        assert status == ConnectionTestStatus.failed

    @mock.patch(
        "fides.api.service.connectors.erasure_email_connector.send_single_erasure_email"
    )
    def test_test_connection_call(
        self, mock_send_email, db, test_attentive_erasure_email_connector
    ):
        test_attentive_erasure_email_connector.test_connection()
        assert mock_send_email.called

        call_kwargs = mock_send_email.call_args.kwargs
        assert call_kwargs["db"] == db
        assert (
            call_kwargs["subject_email"]
            == test_attentive_erasure_email_connector.configuration.secrets[
                "test_email_address"
            ]
        )
        assert call_kwargs["subject_email"] == "processor_address@example.com"
        assert call_kwargs["subject_name"] == "Attentive Email"
        assert call_kwargs["batch_identities"] == ["test_email@example.com"]
        assert call_kwargs["test_mode"]
