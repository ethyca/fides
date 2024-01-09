import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestAppsFlyerConnector:
    def test_connection(self, appsflyer_runner: ConnectorRunner):
        appsflyer_runner.test_connection()

    async def test_access_request(
        self, appsflyer_runner: ConnectorRunner, policy, appsflyer_identity_email: str
    ):
        access_results = await appsflyer_runner.access_request(
            access_policy=policy, identities={"email": appsflyer_identity_email}
        )

        assert len(access_results["appsflyer_instance:user"]) == 10

    async def test_non_strict_erasure_request(
        self,
        appsflyer_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        appsflyer_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results,
        ) = await appsflyer_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": appsflyer_erasure_identity_email},
        )
        assert erasure_results == {
            "appsflyer_external_dataset:appsflyer_external_collection": 0,
            "appsflyer_instance:apps": 0,
            "appsflyer_instance:user": 10,
        }
