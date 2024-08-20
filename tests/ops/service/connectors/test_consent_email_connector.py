from unittest import mock

import pytest

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.connectionconfig import AccessLevel, ConnectionTestStatus
from fides.api.models.privacy_notice import ConsentMechanism, EnforcementLevel
from fides.api.models.privacy_preference import UserConsentPreference
from fides.api.schemas.connection_configuration.connection_secrets_email import (
    AdvancedSettingsWithExtendedIdentityTypes,
    ExtendedEmailSchema,
    ExtendedIdentityTypes,
)
from fides.api.schemas.messaging.messaging import (
    ConsentPreferencesByUser,
    MessagingActionType,
)
from fides.api.schemas.privacy_notice import PrivacyNoticeHistorySchema
from fides.api.schemas.privacy_preference import MinimalPrivacyPreferenceHistorySchema
from fides.api.schemas.privacy_request import Consent
from fides.api.service.connectors.consent_email_connector import (
    GenericConsentEmailConnector,
    filter_user_identities_for_connector,
    get_identity_types_for_connector,
    send_single_consent_email,
)
from fides.api.service.privacy_request.request_runner_service import (
    get_consent_email_connection_configs,
)


class TestConsentEmailConnectorMethods:
    email_and_ljt_readerID_defined = ExtendedEmailSchema(
        third_party_vendor_name="Dawn's Bookstore",
        recipient_email_address="test@example.com",
        advanced_settings=AdvancedSettingsWithExtendedIdentityTypes(
            identity_types=ExtendedIdentityTypes(
                email=True, phone_number=False, cookie_ids=["ljt_readerID"]
            )
        ),
    )

    phone_defined = ExtendedEmailSchema(
        third_party_vendor_name="Dawn's Bookstore",
        recipient_email_address="test@example.com",
        advanced_settings=AdvancedSettingsWithExtendedIdentityTypes(
            identity_types=ExtendedIdentityTypes(
                email=False, phone_number=True, cookie_ids=[]
            )
        ),
    )

    ljt_readerID_defined = ExtendedEmailSchema(
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

    @mock.patch("fides.api.service.connectors.consent_email_connector.dispatch_message")
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
                            Consent(data_use="marketing.advertising", opt_in=False),
                            Consent(
                                data_use="marketing.advertising.first_party",
                                opt_in=True,
                            ),
                        ],
                        privacy_preferences=[],
                    ),
                    ConsentPreferencesByUser(
                        identities={"email": "customer-2@example.com"},
                        consent_preferences=[
                            Consent(data_use="marketing.advertising", opt_in=True),
                            Consent(
                                data_use="marketing.advertising.first_party",
                                opt_in=False,
                            ),
                        ],
                        privacy_preferences=[],
                    ),
                ],
                test_mode=True,
            )

        assert not mock_dispatch.called
        assert (
            exc.value.message
            == "Cannot send an email to third-party vendor. No organization name found."
        )

    @mock.patch("fides.api.service.connectors.consent_email_connector.dispatch_message")
    def test_send_single_consent_email_old_workflow(
        self, mock_dispatch, test_fides_org, db, messaging_config
    ):
        consent_preferences = [
            ConsentPreferencesByUser(
                identities={"email": "customer-1@example.com"},
                consent_preferences=[
                    Consent(data_use="marketing.advertising", opt_in=False),
                    Consent(data_use="marketing.advertising.first_party", opt_in=True),
                ],
                privacy_preferences=[],
            ),
            ConsentPreferencesByUser(
                identities={"email": "customer-2@example.com"},
                consent_preferences=[
                    Consent(data_use="marketing.advertising", opt_in=True),
                    Consent(data_use="marketing.advertising.first_party", opt_in=False),
                ],
                privacy_preferences=[],
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

        assert call_kwargs["service_type"] == "mailgun"
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

    @mock.patch("fides.api.service.connectors.consent_email_connector.dispatch_message")
    def test_send_single_consent_email_preferences_by_privacy_notice(
        self, mock_dispatch, test_fides_org, db, messaging_config
    ):
        consent_preferences = [
            ConsentPreferencesByUser(
                identities={"email": "customer-1@example.com"},
                consent_preferences=[],
                privacy_preferences=[
                    MinimalPrivacyPreferenceHistorySchema(
                        preference=UserConsentPreference.opt_in,
                        privacy_notice_history=PrivacyNoticeHistorySchema(
                            name="Targeted Advertising",
                            notice_key="targeted_advertising",
                            id="test_1",
                            translation_id="12345",
                            consent_mechanism=ConsentMechanism.opt_in,
                            data_uses=["marketing.advertising.first_party.targeted"],
                            enforcement_level=EnforcementLevel.system_wide,
                            version=1.0,
                        ),
                    )
                ],
            ),
            ConsentPreferencesByUser(
                identities={"email": "customer-2@example.com"},
                consent_preferences=[],
                privacy_preferences=[
                    MinimalPrivacyPreferenceHistorySchema(
                        preference=UserConsentPreference.opt_out,
                        privacy_notice_history=PrivacyNoticeHistorySchema(
                            name="Analytics",
                            notice_key="analytics",
                            id="test_2",
                            translation_id="67890",
                            consent_mechanism=ConsentMechanism.opt_out,
                            data_uses=["functional.service.improve"],
                            enforcement_level=EnforcementLevel.system_wide,
                            version=1.0,
                        ),
                    )
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

        assert call_kwargs["service_type"] == "mailgun"
        message_body_params = call_kwargs["message_body_params"]

        assert message_body_params.controller == "Test Org"
        assert message_body_params.third_party_vendor_name == "To whom it may concern"
        assert message_body_params.required_identities == ["email"]
        assert message_body_params.requested_changes == consent_preferences

        assert (
            consent_preferences[0].privacy_preferences[0].privacy_notice_history.name
            == "Targeted Advertising"
        )
        assert (
            consent_preferences[1].privacy_preferences[0].privacy_notice_history.name
            == "Analytics"
        )

        assert (
            call_kwargs["subject_override"]
            == "Test notification of users' consent preference changes from Test Org"
        )

    @mock.patch("fides.api.service.connectors.consent_email_connector.dispatch_message")
    @pytest.mark.usefixtures(
        "test_fides_org",
        "messaging_config",
        "set_notification_service_type_to_twilio_email",
    )
    def test_send_single_consent_email_respects_messaging_service_type(
        self,
        mock_dispatch,
        db,
    ):
        """Ensure `notifications.notification_service_type` property is respected in dispatching consent emails"""
        send_single_consent_email(
            db=db,
            subject_email="test@example.com",
            subject_name="To whom it may concern",
            required_identities=["email"],
            user_consent_preferences=[],
            test_mode=True,
        )

        assert mock_dispatch.called
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["service_type"] == "twilio_email"

    def test_needs_email_old_workflow(
        self,
        test_sovrn_consent_email_connector,
        privacy_request_with_consent_policy,
    ):
        privacy_request_with_consent_policy.consent_preferences = [
            Consent(data_use="marketing.advertising", opt_in=False).model_dump(
                mode="json"
            )
        ]
        assert (
            test_sovrn_consent_email_connector.needs_email(
                {"ljt_readerID": "test_ljt_reader_id"},
                privacy_request_with_consent_policy,
            )
            is True
        )

    def test_needs_email_new_workflow(
        self,
        db,
        test_sovrn_consent_email_connector,
        privacy_request_with_consent_policy,
        privacy_preference_history,
        system,
    ):
        test_sovrn_consent_email_connector.configuration.system_id = system.id
        test_sovrn_consent_email_connector.configuration.save(db)

        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        assert (
            test_sovrn_consent_email_connector.needs_email(
                {"ljt_readerID": "test_ljt_reader_id"},
                privacy_request_with_consent_policy,
            )
            is True
        )

    def test_needs_email_without_any_consent_or_privacy_preferences(
        self,
        test_sovrn_consent_email_connector,
        privacy_request_with_consent_policy,
    ):
        assert (
            test_sovrn_consent_email_connector.needs_email(
                {"ljt_readerID": "test_ljt_reader_id"},
                privacy_request_with_consent_policy,
            )
            is False
        )

    def test_needs_email_without_consent_rules(
        self, test_sovrn_consent_email_connector, privacy_request
    ):
        assert (
            test_sovrn_consent_email_connector.needs_email(
                {"ljt_readerID": "test_ljt_reader_id"},
                privacy_request,
            )
            is False
        )

    def test_needs_email_unsupported_identity_old_workflow(
        self, test_sovrn_consent_email_connector, privacy_request_with_consent_policy
    ):
        privacy_request_with_consent_policy.consent_preferences = [
            Consent(data_use="marketing.advertising", opt_in=False).model_dump(
                mode="json"
            )
        ]
        assert (
            test_sovrn_consent_email_connector.needs_email(
                {"email": "test@example.com"},
                privacy_request_with_consent_policy,
            )
            is False
        )

    def test_needs_email_unsupported_identity_new_workflow(
        self,
        db,
        test_sovrn_consent_email_connector,
        privacy_request_with_consent_policy,
        privacy_preference_history,
    ):
        privacy_preference_history.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history.save(db)

        assert (
            test_sovrn_consent_email_connector.needs_email(
                {"email": "test@example.com"},
                privacy_request_with_consent_policy,
            )
            is False
        )

    def test_needs_email_system_and_notice_data_use_mismatch(
        self,
        db,
        test_sovrn_consent_email_connector,
        privacy_request_with_consent_policy,
        privacy_preference_history_us_ca_provide,
        system,
    ):
        test_sovrn_consent_email_connector.configuration.system_id = system.id
        test_sovrn_consent_email_connector.configuration.save(db)

        privacy_preference_history_us_ca_provide.privacy_request_id = (
            privacy_request_with_consent_policy.id
        )
        privacy_preference_history_us_ca_provide.save(db)

        assert (
            test_sovrn_consent_email_connector.needs_email(
                {"email": "test@example.com"},
                privacy_request_with_consent_policy,
            )
            is False
        )


class TestSovrnConnector:
    def test_generic_identities_for_test_email_property(
        self, sovrn_email_connection_config
    ):
        generic_connector = GenericConsentEmailConnector(sovrn_email_connection_config)
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
        "fides.api.service.connectors.consent_email_connector.send_single_consent_email"
    )
    def test_test_connection_call(
        self, mock_send_email, db, test_sovrn_consent_email_connector
    ):
        """Two of the old workflow preferences and two new workflow preferences added"""
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

        preferences = [
            pref.model_dump() for pref in call_kwargs["user_consent_preferences"]
        ]
        assert len(preferences) == 1
        assert preferences[0]["identities"] == {"ljt_readerID": "test_ljt_reader_id"}
        assert (
            preferences[0]["consent_preferences"][0]["data_use"]
            == "Advertising, Marketing or Promotion"
        )
        assert preferences[0]["consent_preferences"][0]["opt_in"] is False

        assert preferences[0]["consent_preferences"][1]["data_use"] == "Functional"
        assert preferences[0]["consent_preferences"][1]["opt_in"] is True

        assert (
            preferences[0]["privacy_preferences"][0]["preference"]
            == UserConsentPreference.opt_in
        )
        assert (
            preferences[0]["privacy_preferences"][0]["privacy_notice_history"]["name"]
            == "Targeted Advertising"
        )

        assert (
            preferences[0]["privacy_preferences"][1]["preference"]
            == UserConsentPreference.opt_out
        )
        assert (
            preferences[0]["privacy_preferences"][1]["privacy_notice_history"]["name"]
            == "Analytics"
        )

        assert call_kwargs["test_mode"]
