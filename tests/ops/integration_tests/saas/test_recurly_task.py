import pytest

from fides.api.models.policy import Policy
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

    # async def test_strict_erasure_request(
    #     self,
    #     recurly_runner: ConnectorRunner,
    #     policy: Policy,
    #     erasure_policy_string_rewrite: Policy,
    #     recurly_erasure_identity_email: str,
    #     recurly_erasure_data,
    # ):
    #     (
    #         access_results,
    #         erasure_results,
    #     ) = await recurly_runner.strict_erasure_request(
    #         access_policy=policy,
    #         erasure_policy=erasure_policy_string_rewrite,
    #         identities={"email": recurly_erasure_identity_email},
    #     )

    async def test_non_strict_erasure_request(
        self,
        recurly_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        recurly_erasure_identity_email: str,
        recurly_erasure_data,
        recurly_client
    ):
        (
            access_results,
            erasure_results,
        ) = await recurly_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": recurly_erasure_identity_email},
        )

        assert erasure_results == {
            "recurly_instance:accounts": 1,
            "recurly_instance:billing_info": 0,
            "recurly_instance:shipping_address": 1,
        }

        response = recurly_client.get_accounts(recurly_erasure_identity_email)        
        # Check if user details is updated or not
        account = response.json()
        account_id = account['data'][0]['id']
        assert account['data'][0]["state"] == "inactive"        

        address_response = recurly_client.get_shipping_address(account_id)
        address_data = address_response.json()
        assert address_data['data'] == []        

        billing_response = recurly_client.get_billing_info(account_id)
        assert billing_response.status_code == 404       