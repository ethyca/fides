import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestGongConnector:
    def test_connection(self, gong_runner: ConnectorRunner):
        gong_runner.test_connection()

    async def test_access_request_email(
        self, gong_runner: ConnectorRunner, policy, gong_identity_email: str
    ):
        access_results = await gong_runner.access_request(
            access_policy=policy, identities={"email": gong_identity_email}
        )
        
    async def test_access_request_phone_number(
        self, gong_runner: ConnectorRunner, policy, gong_identity_phone_number: str
    ):
        access_results = await gong_runner.access_request(
            access_policy=policy, identities={"phoneNumber": gong_identity_phone_number}
        )

    # async def test_non_strict_erasure_request(
    #     self,
    #     gong_runner: ConnectorRunner,
    #     policy: Policy,
    #     erasure_policy_string_rewrite: Policy,
    #     gong_erasure_identity_email: str,
    #     gong_erasure_data,
    # ):
    #     (
    #         access_results,
    #         erasure_results,
    #     ) = await gong_runner.non_strict_erasure_request(
    #         access_policy=policy,
    #         erasure_policy=erasure_policy_string_rewrite,
    #         identities={"email": gong_erasure_identity_email},
    #     )