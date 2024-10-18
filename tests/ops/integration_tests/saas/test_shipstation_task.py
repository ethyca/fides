import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="move to plus in progress")
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

        key = shipstation_runner.dataset_config.fides_key
        external_id = shipstation_runner.external_references["customer_id"]
        access_request = await shipstation_runner.access_request(
            access_policy=policy,
            identities={"email": shipstation_identity_email},
        )

        assert len(access_request[f"{key}:customer"]) == 1
        assert len(access_request[f"{key}:orders"]) == 2

        for customer in access_request[f"{key}:customer"]:
            assert customer["customerId"] == int(external_id)

        for order in access_request[f"{key}:orders"]:
            assert order["customerId"] == int(external_id)
