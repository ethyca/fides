import pytest

from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestRecurlyConnector:
    def test_connection(self, recurly_runner: ConnectorRunner):
        recurly_runner.test_connection()

    async def test_access_request(
        self, recurly_runner: ConnectorRunner, policy, recurly_identity_email: str
    ):
        access_results = await recurly_runner.access_request(
            access_policy=policy, identities={"email": recurly_identity_email}
        )

        assert len(access_results["recurly_instance:accounts"]) == 1
        account = access_results["recurly_instance:accounts"][0]
        assert account["email"] == recurly_identity_email

        for billing_info in access_results["recurly_instance:billing_info"]:
            assert billing_info["account_id"] == account["id"]

        for shipping_address in access_results["recurly_instance:shipping_address"]:
            assert shipping_address["account_id"] == account["id"]
