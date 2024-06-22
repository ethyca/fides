import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class Testtwilio_smsConnector:
    def test_connection(self, twilio_sms_runner: ConnectorRunner):
        twilio_sms_runner.test_connection()

    async def test_access_request(
        self, twilio_sms_runner: ConnectorRunner, policy, twilio_sms_identity_phone_number: str,
        twilio_sms_add_data,
    ):
        assert twilio_sms_identity_phone_number.startswith('+') and twilio_sms_identity_phone_number[1:].isdigit(), "Invalid phone number format"
        access_results = await twilio_sms_runner.access_request(
            access_policy=policy, identities={"phone_number": twilio_sms_identity_phone_number}
        )
        for user in access_results["twilio_sms_instance:user"]:
            assert user["to"] == twilio_sms_identity_phone_number or user["from"] == twilio_sms_identity_phone_number


    async def test_non_strict_erasure_request(
        self,
        twilio_sms_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        twilio_sms_erasure_identity_phone_number: str,
        twilio_sms_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await twilio_sms_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"phone_number": twilio_sms_erasure_identity_phone_number},
        )
        #
        assert erasure_results == {"twilio_sms_instance:user": 2}
