import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestShipstationConnector:
    def test_connection(self, shipstation_runner: ConnectorRunner):
        shipstation_runner.test_connection()

    async def test_access_request(
        self,
        shipstation_runner: ConnectorRunner,
        policy: Policy,
        shipstation_identity_email: str,
    ):
        access_results = await shipstation_runner.access_request(
            access_policy=policy,
            identities={"email": shipstation_identity_email},
        )
        print(access_results)
        assert len(access_results["shipstation_instance:get_customer"]) == 1
        assert (
            access_results["shipstation_instance:get_customer"][0]["email"]
            == shipstation_identity_email
        )
