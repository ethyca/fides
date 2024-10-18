import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestCheckrConnector:
    def test_connection(self, checkr_runner: ConnectorRunner):
        checkr_runner.test_connection()

    async def test_access_request(
        self, checkr_runner: ConnectorRunner, policy, checkr_identity_email: str
    ):
        access_results = await checkr_runner.access_request(
            access_policy=policy, identities={"email": checkr_identity_email}
        )
        assert (
            access_results["checkr_instance:user"][0]["email"]
        ) == checkr_identity_email

    async def test_non_strict_erasure_request(
        self,
        checkr_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        checkr_erasure_identity_email: str,
        checkr_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await checkr_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": checkr_erasure_identity_email},
        )
        assert erasure_results == {"checkr_instance:user": 1}
