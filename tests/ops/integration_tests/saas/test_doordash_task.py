import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestDoordashConnector:
    def test_connection(self, doordash_runner: ConnectorRunner):
        doordash_runner.test_connection()

    async def test_access_request(
        self,
        doordash_runner: ConnectorRunner,
        policy: Policy,
        doordash_identity_email: str,
    ):
        await doordash_runner.access_request(
            access_policy=policy, identities={"email": doordash_identity_email}
        )
