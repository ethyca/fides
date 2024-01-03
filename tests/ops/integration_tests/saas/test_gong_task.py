import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestGongConnector:
    def test_connection(self, gong_runner: ConnectorRunner):
        gong_runner.test_connection()

    async def test_access_request(
        self,
        gong_runner: ConnectorRunner,
        policy,
        gong_identity_email: str,
        gong_identity_name: str,
    ):
        access_results = await gong_runner.access_request(
            access_policy=policy, identities={"email": gong_identity_email}
        )

        # verify that the customer data contains the name that corresponds to the identity email
        assert len(access_results["gong_instance:user"]) == 1
        assert len(access_results["gong_instance:user"][0]["customerData"]) == 1
        objects = access_results["gong_instance:user"][0]["customerData"][0]["objects"]
        for obj in objects:
            assert obj["fields"][0] == {"name": "fullName", "value": gong_identity_name}

    async def test_non_strict_erasure_request(
        self,
        gong_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        gong_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results,
        ) = await gong_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": gong_erasure_identity_email},
        )
        assert erasure_results == {"gong_instance:user": 1}
