import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestAda_ChatbotConnector:
    def test_connection(self, ada_chatbot_runner: ConnectorRunner):
        ada_chatbot_runner.test_connection()

    async def test_access_request(
        self, ada_chatbot_runner: ConnectorRunner, policy, ada_chatbot_identity_email: str
    ):
        access_results = await ada_chatbot_runner.access_request(
            access_policy=policy, identities={"email": ada_chatbot_identity_email}
        )

        # verify we only returned data for our identity email
        assert (
            access_results["ada_chatbot_instance:conversations"][0]["variables"]["email"]
            == ada_chatbot_identity_email
        )