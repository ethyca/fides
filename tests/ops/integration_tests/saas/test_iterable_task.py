import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestIterableConnector:
    def test_connection(self, iterable_runner: ConnectorRunner):
        iterable_runner.test_connection()

    async def test_non_strict_erasure_request(
        self,
        iterable_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        iterable_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results,
        ) = await iterable_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": iterable_erasure_identity_email},
        )
        assert erasure_results == {"iterable_instance:user": 1}
