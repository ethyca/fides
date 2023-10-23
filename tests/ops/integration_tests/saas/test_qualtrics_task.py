import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestQualtricsConnector:
    def test_connection(self, qualtrics_runner: ConnectorRunner):
        qualtrics_runner.test_connection()

    async def test_access_request(
        self, qualtrics_runner: ConnectorRunner, policy, qualtrics_identity_email: str
    ):
        access_results = await qualtrics_runner.access_request(
            access_policy=policy, identities={"email": qualtrics_identity_email}
        )

        for contacts in access_results["qualtrics_instance:search_directory_contact"]:
            assert contacts["email"] == qualtrics_identity_email