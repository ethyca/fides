import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestTalkableConnector:
    def test_connection(self, talkable_runner: ConnectorRunner):
        talkable_runner.test_connection()

    async def test_access_request(
        self, talkable_runner: ConnectorRunner, policy, talkable_identity_email: str
    ):
        access_results = await talkable_runner.access_request(
            access_policy=policy, identities={"email": talkable_identity_email}
        )
        
        # verify we only returned data for our identity email
        assert (
            access_results["talkable_instance:person"][0]["email"]
            == talkable_identity_email
        )

    async def test_non_strict_erasure_request(
        self,
        talkable_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        talkable_erasure_identity_email: str,
        talkable_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await talkable_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": talkable_erasure_identity_email},
        )

        assert erasure_results == {
            "talkable_instance:person": 1,
        }
