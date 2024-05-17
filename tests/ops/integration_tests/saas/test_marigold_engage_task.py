import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestMarigoldEngageConnector:
    def test_connection(self, marigold_engage_runner: ConnectorRunner):
        marigold_engage_runner.test_connection()

    async def test_access_request(
        self,
        marigold_engage_runner: ConnectorRunner,
        policy,
        marigold_engage_identity_email: str,
    ):
        access_results = await marigold_engage_runner.access_request(
            access_policy=policy, identities={"email": marigold_engage_identity_email}
        )
        for user in access_results["marigold_engage_instance:user"]:
            assert user["keys"]["email"] == marigold_engage_identity_email

    async def test_non_strict_erasure_request(
        self,
        marigold_engage_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        marigold_engage_erasure_identity_email: str,
        marigold_engage_erasure_data,
    ):
        (
            _,
            erasure_results,
        ) = await marigold_engage_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": marigold_engage_erasure_identity_email},
        )
        assert erasure_results == {"marigold_engage_instance:user": 1}
