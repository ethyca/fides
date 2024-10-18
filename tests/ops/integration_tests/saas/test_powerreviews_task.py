import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestPowerReviewsConnector:
    def test_connection(self, powerreviews_runner: ConnectorRunner):
        powerreviews_runner.test_connection()

    async def test_non_strict_erasure_request(
        self,
        powerreviews_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        powerreviews_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results,
        ) = await powerreviews_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": powerreviews_erasure_identity_email},
        )
        assert erasure_results == {"powerreviews_instance:user": 1}
