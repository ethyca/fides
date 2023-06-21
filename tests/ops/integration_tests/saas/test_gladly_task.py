import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestGladlyConnector:
    def test_connection(self, gladly_runner: ConnectorRunner):
        gladly_runner.test_connection()

    async def test_access_request_with_email(
        self, gladly_runner: ConnectorRunner, policy, gladly_identity_email: str
    ):
        access_results = await gladly_runner.access_request(
            access_policy=policy, identities={"email": gladly_identity_email}
        )
        assert access_results["gladly_instance:customer"][0]["emails"] == [
            {"normalized": gladly_identity_email, "original": gladly_identity_email}
        ]

    async def test_access_request_with_phone_number(
        self, gladly_runner: ConnectorRunner, policy, gladly_identity_phone_number: str
    ):
        access_results = await gladly_runner.access_request(
            access_policy=policy,
            identities={"phone_number": gladly_identity_phone_number},
        )
        assert access_results["gladly_instance:customer"][0]["phones"] == [
            {
                "normalized": gladly_identity_phone_number,
                "original": gladly_identity_phone_number,
                "regionCode": "US",
                "type": "MOBILE",
            }
        ]

    async def test_non_strict_erasure_request(
        self,
        gladly_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite_name_and_email: Policy,
        gladly_erasure_identity_email: str,
        gladly_erasure_data,
        gladly_client,
    ):
        (
            access_results,
            erasure_results,
        ) = await gladly_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite_name_and_email,
            identities={"email": gladly_erasure_identity_email},
        )

        assert erasure_results == {
            "gladly_instance:customer": 1,
        }

        response = gladly_client.get_customer(gladly_erasure_identity_email)
        assert response.json() == []
