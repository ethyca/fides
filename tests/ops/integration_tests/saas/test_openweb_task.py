import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestOpenWebConnector:
    def test_connection(self, openweb_runner: ConnectorRunner):
        openweb_runner.test_connection()
        

    # async def test_access_request(
    #     self, openweb_runner: ConnectorRunner, policy, openweb_identity_email: str
    # ):
    #     access_results = await openweb_runner.access_request(
    #         access_policy=policy, identities={"email": openweb_identity_email}
    #     )

    # async def test_non_strict_erasure_request(
    #     self,
    #     openweb_runner: ConnectorRunner,
    #     policy: Policy,

    #     erasure_policy_string_rewrite: Policy,
    #     openweb_erasure_identity_email: str,
    # ):
    #     (
    #         # access_results,
    #         _,
    #         erasure_results,
    #     ) = await openweb_runner.non_strict_erasure_request(
    #         access_policy=policy,
    #         erasure_policy=erasure_policy_string_rewrite,
    #         # identities={"email": openweb_erasure_identity_email},
    #     )
    #     assert erasure_results == {"openweb_instance:user": 1}