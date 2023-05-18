import pytest

from fides.api.ops.models.policy import Policy
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

    async def test_access_request_with_phone_number(
        self, gladly_runner: ConnectorRunner, policy, gladly_identity_phone_number: str
    ):
        access_results = await gladly_runner.access_request(
            access_policy=policy, identities={"phone_number": gladly_identity_phone_number}
        )

    # async def test_strict_erasure_request(
    #     self,
    #     gladly_runner: ConnectorRunner,
    #     policy: Policy,
    #     erasure_policy_string_rewrite: Policy,
    #     gladly_erasure_identity_email: str,
    #     gladly_erasure_data,
    # ):
    #     (
    #         access_results,
    #         erasure_results,
    #     ) = await gladly_runner.strict_erasure_request(
    #         access_policy=policy,
    #         erasure_policy=erasure_policy_string_rewrite,
    #         identities={"email": gladly_erasure_identity_email},
    #     )

    async def test_non_strict_erasure_request(
        self,
        gladly_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        gladly_erasure_identity_email: str,
        gladly_erasure_data,
        gladly_client
    ):
        (
            access_results,
            erasure_results,
        ) = await gladly_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": gladly_erasure_identity_email},
        )

        assert erasure_results == {
            "gladly_instance:customer": 1,
        }

        response = gladly_client.get_customer(gladly_erasure_identity_email)
        # Check if user details is updated or not
        customer = response.json()[0]
        assert customer["name"] == "MASKED"