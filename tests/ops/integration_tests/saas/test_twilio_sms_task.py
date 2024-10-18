import pytest

from fides.api.common_exceptions import TraversalError
from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestTwilioSMSConnector:
    def test_connection(self, twilio_sms_runner: ConnectorRunner):
        twilio_sms_runner.test_connection()

    async def test_access_request(
        self,
        twilio_sms_runner: ConnectorRunner,
        policy,
        twilio_sms_identity_phone_number: str,
        twilio_sms_add_data,
    ):
        access_results = await twilio_sms_runner.access_request(
            access_policy=policy,
            identities={"phone_number": twilio_sms_identity_phone_number},
        )
        for message in access_results["twilio_sms_instance:message"]:
            assert (
                message["to"] == twilio_sms_identity_phone_number
                or message["from"] == twilio_sms_identity_phone_number
            )

    async def test_access_request_with_email(
        self,
        twilio_sms_runner: ConnectorRunner,
        policy,
    ):
        with pytest.raises(TraversalError):
            await twilio_sms_runner.access_request(
                access_policy=policy, identities={"email": "customer-1@example.com"}
            )

    async def test_non_strict_erasure_request_with_email(
        self,
        twilio_sms_runner: ConnectorRunner,
        policy,
        twilio_sms_erasure_identity_phone_number: str,
        erasure_policy_string_rewrite: Policy,
    ):
        with pytest.raises(TraversalError):
            await twilio_sms_runner.non_strict_erasure_request(
                access_policy=policy,
                erasure_policy=erasure_policy_string_rewrite,
                identities={"email": "customer-1@example.com"},
            )

    async def test_non_strict_erasure_request(
        self,
        twilio_sms_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        twilio_sms_erasure_identity_phone_number: str,
    ):
        (
            _,
            erasure_results,
        ) = await twilio_sms_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"phone_number": twilio_sms_erasure_identity_phone_number},
        )
        assert erasure_results == {"twilio_sms_instance:message": 2}
