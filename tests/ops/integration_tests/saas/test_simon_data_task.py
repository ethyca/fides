import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestSimonDataConnector:
    def test_connection(self, simon_data_runner: ConnectorRunner):
        simon_data_runner.test_connection()

    async def test_non_strict_erasure_request(
        self,
        simon_data_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        simon_data_erasure_identity_email: str,
        simon_data_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await simon_data_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": simon_data_erasure_identity_email},
        )
        assert erasure_results == {"simon_data_instance:contact": 1}
