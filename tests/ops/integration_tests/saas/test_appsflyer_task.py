### Marc you are not done yet. Remove this comment only when you're DONE with this test file!
### Do you have any extraneous tests?
### All tests passing?

import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestAppsflyerConnector:
    def test_connection(self, appsflyer_runner: ConnectorRunner):
        appsflyer_runner.test_connection()

    async def test_access_request(
        self, appsflyer_runner: ConnectorRunner, policy, appsflyer_identity_email: str
    ):
        access_results = await appsflyer_runner.access_request(
            access_policy=policy, identities={"email": appsflyer_identity_email}
        )

    async def test_strict_erasure_request(
        self,
        appsflyer_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        appsflyer_erasure_identity_email: str,
        appsflyer_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await appsflyer_runner.strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": appsflyer_erasure_identity_email},
        )

    async def test_non_strict_erasure_request(
        self,
        appsflyer_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        appsflyer_erasure_identity_email: str,
        appsflyer_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await appsflyer_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": appsflyer_erasure_identity_email},
        )
