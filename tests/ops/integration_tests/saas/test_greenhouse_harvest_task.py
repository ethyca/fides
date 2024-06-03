import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class Testgreenhouse_harvestConnector:
    def test_connection(self, greenhouse_harvest_runner: ConnectorRunner):
        greenhouse_harvest_runner.test_connection()

    async def test_access_request(
        self,
        greenhouse_harvest_runner: ConnectorRunner,
        policy: Policy,
        greenhouse_harvest_identity_email: str,
    ):
        access_results = await greenhouse_harvest_runner.access_request(
            access_policy=policy, identities={"email": greenhouse_harvest_identity_email}
        )
        assert (access_results["greenhouse_harvest:user"])
        # assert here

    async def test_non_strict_erasure_request(
        self,
        greenhouse_harvest_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        greenhouse_harvest_erasure_identity_email: str,
        greenhouse_harvest_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await greenhouse_harvest_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": greenhouse_harvest_erasure_identity_email},
        )
