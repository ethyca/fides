import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestQualtricsConnector:
    def test_connection(self, qualtrics_runner: ConnectorRunner):
        qualtrics_runner.test_connection()

    async def test_non_strict_erasure_request(
        self,
        qualtrics_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        qualtrics_erasure_identity_email: str,
    ):
        (
            access_results,
            erasure_results,
        ) = await qualtrics_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": qualtrics_erasure_identity_email},
        )
        assert erasure_results == {"qualtrics_instance:user": 1}
