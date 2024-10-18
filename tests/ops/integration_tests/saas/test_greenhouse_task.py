import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestGreenhouseConnector:
    def test_connection(self, greenhouse_runner: ConnectorRunner):
        greenhouse_runner.test_connection()

    async def test_access_request(
        self,
        greenhouse_runner: ConnectorRunner,
        policy: Policy,
        greenhouse_identity_email: str,
    ):
        access_results = await greenhouse_runner.access_request(
            access_policy=policy, identities={"email": greenhouse_identity_email}
        )
        assert (
            access_results["greenhouse_instance:user"][0]["email_addresses"][0]["value"]
        ) == greenhouse_identity_email

    async def test_non_strict_erasure_request(
        self,
        greenhouse_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        greenhouse_erasure_identity_email: str,
        greenhouse_erasure_data,
    ):
        (
            _,
            erasure_results,
        ) = await greenhouse_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": greenhouse_erasure_identity_email},
        )
        assert erasure_results == {"greenhouse_instance:user": 1}
