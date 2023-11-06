import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestAda_chatbotConnector:
    def test_connection(self, ada_chatbot_runner: ConnectorRunner):
        ada_chatbot_runner.test_connection()

    async def test_access_request(
        self,
        ada_chatbot_runner: ConnectorRunner,
        policy,
        ada_chatbot_identity_email: str,
    ):
        access_results = await ada_chatbot_runner.access_request(
            access_policy=policy, identities={"email": ada_chatbot_identity_email}
        )
        ## assert for email field

    async def test_non_strict_erasure_request(
        self,
        ada_chatbot_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        ada_chatbot_erasure_identity_email: str,
        ada_chatbot_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await ada_chatbot_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": ada_chatbot_erasure_identity_email},
        )
        assert erasure_results == {"ada_chatbot_instance:chatter": 1}
