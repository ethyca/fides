import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestPowerReviewsConnector:
    def test_connection(self, power_reviews_runner: ConnectorRunner):
        power_reviews_runner.test_connection()


    async def test_non_strict_erasure_request(
        self,
        power_reviews_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        power_reviews_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results,
        ) = await power_reviews_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": power_reviews_erasure_identity_email},
        )
        # We set the email to 1 since its 1 request only(?)
        assert erasure_results == {"power_reviews_instance:privacy": 1}
