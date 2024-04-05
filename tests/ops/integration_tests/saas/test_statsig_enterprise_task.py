import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestStatsigEnterpriseConnector:
    def test_connection(self, statsig_enterprise_runner: ConnectorRunner):
        statsig_enterprise_runner.test_connection()

    @pytest.mark.skip(reason="Enterprise account only")
    async def test_non_strict_erasure_request(
        self,
        statsig_enterprise_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        statsig_enterprise_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results,
        ) = await statsig_enterprise_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": statsig_enterprise_erasure_identity_email},
        )
        assert erasure_results == {"statsig_enterprise_instance:user": 1}
