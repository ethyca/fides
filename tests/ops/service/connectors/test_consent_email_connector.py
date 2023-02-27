from unittest import mock

import pytest

from fides.api.ops.common_exceptions import MessageDispatchException
from fides.api.ops.models.connectionconfig import AccessLevel, ConnectionTestStatus
from fides.api.ops.schemas.connection_configuration.connection_secrets_sovrn import (
    AdvancedSettingsWithExtendedIdentityTypes,
    ExtendedConsentEmailSchema,
    ExtendedIdentityTypes,
)
from fides.api.ops.schemas.messaging.messaging import (
    ConsentPreferencesByUser,
    MessagingActionType,
)
from fides.api.ops.schemas.privacy_request import Consent
from fides.api.ops.service.connectors.consent_email_connector import (
    GenericEmailConsentConnector,
    filter_user_identities_for_connector,
    get_consent_email_connection_configs,
    get_identity_types_for_connector,
    send_single_consent_email,
)


class TestEmailConsentConnectorMethods:
    email_and_ljt_readerID_defined = ExtendedConsentEmailSchema(
        third_party_vendor_name="Dawn's Bookstore",
        recipient_email_address="test@example.com",
        advanced_settings=AdvancedSettingsWithExtendedIdentityTypes(
            identity_types=ExtendedIdentityTypes(
                email=True, phone_number=False, cookie_ids=["ljt_readerID"]
            )
        ),
    )

    phone_defined = ExtendedConsentEmailSchema(
        third_party_vendor_name="Dawn's Bookstore",
        recipient_email_address="test@example.com",
        advanced_settings=AdvancedSettingsWithExtendedIdentityTypes(
            identity_types=ExtendedIdentityTypes(
                email=False, phone_number=True, cookie_ids=[]
            )
        ),
    )

    ljt_readerID_defined = ExtendedConsentEmailSchema(
        third_party_vendor_name="Dawn's Bookstore",
        recipient_email_address="test@example.com",
        advanced_settings=AdvancedSettingsWithExtendedIdentityTypes(
            identity_types=ExtendedIdentityTypes(
                email=False, phone_number=False, cookie_ids=["ljt_readerID"]
            )
        ),
    )

    def test_get_consent_email_connection_configs_none(self, db):
        assert not get_consent_email_connection_configs(db).first()

    def test_get_consent_email_connection_configs(
        self, db, sovrn_email_connection_config
    ):
        assert get_consent_email_connection_configs(db).count() == 1
        assert (
            get_consent_email_connection_configs(db).first().name
            == sovrn_email_connection_config.name
        )

        sovrn_email_connection_config.disabled = True
        sovrn_email_connection_config.save(db=db)
        assert not get_consent_email_connection_configs(db).first()

    def test_get_consent_email_connection_configs_read_only(
        self, db, sovrn_email_connection_config
    ):
        sovrn_email_connection_config.access = AccessLevel.read
        sovrn_email_connection_config.save(db=db)
        assert not get_consent_email_connection_configs(db).first()

    @pytest.mark.parametrize(
        "email_schema, identity_types",
        [
            (email_and_ljt_readerID_defined, ["ljt_readerID", "email"]),
            (phone_defined, ["phone_number"]),
            (ljt_readerID_defined, ["ljt_readerID"]),
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
                email_and_ljt_readerID_defined,
                {"email": "test@example.com"},
                {"email": "test@example.com"},
            ),
            (
                email_and_ljt_readerID_defined,
                {"ljt_readerID": "12345"},
                {"ljt_readerID": "12345"},
            ),
            (email_and_ljt_readerID_defined, {"phone_number": "333-222-2221"}, {}),
            (
                email_and_ljt_readerID_defined,
                {
                    "phone_number": "333-222-2221",
                    "email": "test@example.com",
                    "ljt_readerID": "12345",
                },
                {"email": "test@example.com", "ljt_readerID": "12345"},
            ),
            (phone_defined, {"email": "test@example.com"}, {}),
            (phone_defined, {"ljt_readerID": "12345"}, {}),
            (
                phone_defined,
                {"phone_number": "333-222-2221"},
                {"phone_number": "333-222-2221"},
            ),
            (ljt_readerID_defined, {"email": "test@example.com"}, {}),
            (
                ljt_readerID_defined,
                {"ljt_readerID": "12345"},
                {"ljt_readerID": "12345"},
            ),
            (ljt_readerID_defined, {"phone_number": "333-222-2221"}, {}),
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
        "fides.api.ops.service.connectors.consent_email_connector.dispatch_message"
    )
    def test_send_single_consent_email_no_org_defined(self, mock_dispatch, db):
        with pytest.raises(MessageDispatchException) as exc:
            send_single_consent_email(
                db=db,
                subject_email="test@example.com",
                subject_name="To whom it may concern",
                required_identities=["email"],
                user_consent_preferences=[
                    ConsentPreferencesByUser(
                        identities={"email": "customer-1@example.com"},
                        consent_preferences=[
                            Consent(data_use="advertising", opt_in=False),
                            Consent(data_use="advertising.first_party", opt_in=True),
                        ],
                    ),
                    ConsentPreferencesByUser(
                        identities={"email": "customer-2@example.com"},
                        consent_preferences=[
                            Consent(data_use="advertising", opt_in=True),
                            Consent(data_use="advertising.first_party", opt_in=False),
                        ],
                    ),
                ],
                test_mode=True,
            )

        assert not mock_dispatch.called
        assert (
            exc.value.message
            == "Cannot send an email requesting consent preference changes to third-party vendor. No organization name found."
        )

    @mock.patch(
        "fides.api.ops.service.connectors.consent_email_connector.dispatch_message"
    )
    def test_send_single_consent_email(self, mock_dispatch, test_fides_org, db):
        consent_preferences = [
            ConsentPreferencesByUser(
                identities={"email": "customer-1@example.com"},
                consent_preferences=[
                    Consent(data_use="advertising", opt_in=False),
                    Consent(data_use="advertising.first_party", opt_in=True),
                ],
            ),
            ConsentPreferencesByUser(
                identities={"email": "customer-2@example.com"},
                consent_preferences=[
                    Consent(data_use="advertising", opt_in=True),
                    Consent(data_use="advertising.first_party", opt_in=False),
                ],
            ),
        ]

        send_single_consent_email(
            db=db,
            subject_email="test@example.com",
            subject_name="To whom it may concern",
            required_identities=["email"],
            user_consent_preferences=consent_preferences,
            test_mode=True,
        )

        assert mock_dispatch.called
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["db"] == db
        assert (
            call_kwargs["action_type"]
            == MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT
        )
        assert call_kwargs["to_identity"].email == "test@example.com"
        assert call_kwargs["to_identity"].phone_number is None
        assert call_kwargs["to_identity"].ga_client_id is None

        assert call_kwargs["service_type"] == "MAILGUN"
        message_body_params = call_kwargs["message_body_params"]

        assert message_body_params.controller == "Test Org"
        assert message_body_params.third_party_vendor_name == "To whom it may concern"
        assert message_body_params.required_identities == ["email"]
        assert message_body_params.requested_changes == consent_preferences

        assert (
            consent_preferences[0].consent_preferences[0].data_use
            == "Advertising, Marketing or Promotion"
        )
        assert (
            consent_preferences[0].consent_preferences[1].data_use
            == "First Party Advertising"
        )

        assert (
            call_kwargs["subject_override"]
            == "Test notification of users' consent preference changes from Test Org"
        )


class TestSovrnEmailConsentConnector:
    def test_generic_identities_for_test_email_property(
        self, sovrn_email_connection_config
    ):
        generic_connector = GenericEmailConsentConnector(sovrn_email_connection_config)
        assert generic_connector.identities_for_test_email == {
            "email": "test_email@example.com"
        }

    def test_sovrn_identities_for_test_email_property(
        self, test_sovrn_consent_email_connector
    ):
        assert test_sovrn_consent_email_connector.identities_for_test_email == {
            "ljt_readerID": "test_ljt_reader_id"
        }

    def test_required_identities_property(self, test_sovrn_consent_email_connector):
        assert test_sovrn_consent_email_connector.required_identities == [
            "ljt_readerID"
        ]

    def test_connection_no_test_email_address(
        self, db, test_sovrn_consent_email_connector
    ):
        # Set test_email_address to None
        connection_config = test_sovrn_consent_email_connector.configuration
        connection_config.secrets["test_email_address"] = None
        connection_config.save(db=db)

        status = test_sovrn_consent_email_connector.test_connection()
        assert status == ConnectionTestStatus.failed

    @mock.patch(
        "fides.api.ops.service.connectors.consent_email_connector.send_single_consent_email"
    )
    def test_test_connection_call(
        self, mock_send_email, db, test_sovrn_consent_email_connector
    ):
        test_sovrn_consent_email_connector.test_connection()
        assert mock_send_email.called

        call_kwargs = mock_send_email.call_args.kwargs
        assert call_kwargs["db"] == db
        assert (
            call_kwargs["subject_email"]
            == test_sovrn_consent_email_connector.configuration.secrets[
                "test_email_address"
            ]
        )
        assert call_kwargs["subject_email"] == "processor_address@example.com"
        assert call_kwargs["subject_name"] == "Sovrn"
        assert call_kwargs["required_identities"] == ["ljt_readerID"]
        assert [pref.dict() for pref in call_kwargs["user_consent_preferences"]] == [
            {
                "identities": {"ljt_readerID": "test_ljt_reader_id"},
                "consent_preferences": [
                    {
                        "data_use": "Advertising, Marketing or Promotion",
                        "data_use_description": None,
                        "opt_in": False,
                        "has_gpc_flag": False,
                        "conflicts_with_gpc": False,
                    },
                    {
                        "data_use": "Improve the capability",
                        "data_use_description": None,
                        "opt_in": True,
                        "has_gpc_flag": False,
                        "conflicts_with_gpc": False,
                    },
                ],
            }
        ]
        assert call_kwargs["test_mode"]
