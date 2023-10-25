import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestIterateConnector:
    def test_connection(self, iterate_runner: ConnectorRunner):
        iterate_runner.test_connection()

    async def test_access_request(
        self, iterate_runner: ConnectorRunner, policy, iterate_identity_email: str
    ):
        access_results = await iterate_runner.access_request(
            access_policy=policy, identities={"email": iterate_identity_email}
        )
        assert (
            access_results["iterate_instance:user"][0]["emails"][0]["email"]
            == iterate_identity_email
        )

    @pytest.mark.skip(reason="Unable to create erasure data")
    async def test_strict_erasure_request(
        self,
        iterate_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        iterate_erasure_identity_email: str,
    ):
        (
            access_results,
            erasure_results,
        ) = await iterate_runner.strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": iterate_erasure_identity_email},
        )

        assert erasure_results == {
            "iterate_instance:company": 0,
            "iterate_instance:user": 1,
        }
