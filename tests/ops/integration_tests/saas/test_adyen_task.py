import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestAdyenConnector:
    def test_connection(self, adyen_runner: ConnectorRunner):
        adyen_runner.test_connection()

    # async def test_access_request(
    #     self, adyen_runner: ConnectorRunner, policy, adyen_identity_email: str
    # ):
    #     access_results = await adyen_runner.access_request(
    #         access_policy=policy, identities={"email": adyen_identity_email}
    #     )
        ## MARC remove this next line
    #@pytest.mark.skip("Enterprise account only")
    async def test_non_strict_erasure_request(
        self,
        adyen_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        adyen_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results, 
            ) = await adyen_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": adyen_erasure_identity_email},
        )
        # assert erasure_results == {"adyen_instance:user":1}
