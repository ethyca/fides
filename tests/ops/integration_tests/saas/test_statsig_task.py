import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestStatsigConnector:
    def test_connection(self, statsig_runner: ConnectorRunner):
        statsig_runner.test_connection()

    async def test_strict_erasure_request(
        self,
        statsig_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        statsig_erasure_identity_email: str,
        statsig_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await statsig_runner.strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": statsig_erasure_identity_email},
        )
        assert erasure_results == {"statsig_instance:user": 1}

    # async def test_non_strict_erasure_request(
    #     self,
    #     statsig_runner: ConnectorRunner,
    #     policy: Policy,
    #     erasure_policy_string_rewrite: Policy,
    #     statsig_erasure_identity_email: str,
    #     statsig_erasure_data,
    # ):
    #     (
    #         access_results,
    #         erasure_results,
    #     ) = await statsig_runner.non_strict_erasure_request(
    #         access_policy=policy,
    #         erasure_policy=erasure_policy_string_rewrite,
    #         identities={"email": statsig_erasure_identity_email},
    #     )
