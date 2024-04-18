import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestMarigoldConnector:
    def test_connection(self, marigold_runner: ConnectorRunner):
        marigold_runner.test_connection()

    async def test_access_request(
        self, marigold_runner: ConnectorRunner, policy, marigold_identity_email: str
    ):
        access_results = await marigold_runner.access_request(
            access_policy=policy, identities={"email": marigold_identity_email}
        )

    async def test_strict_erasure_request(
        self,
        marigold_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        marigold_erasure_identity_email: str,
        marigold_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await marigold_runner.strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": marigold_erasure_identity_email},
        )

    async def test_non_strict_erasure_request(
        self,
        marigold_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        marigold_erasure_identity_email: str,
        marigold_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await marigold_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": marigold_erasure_identity_email},
        )