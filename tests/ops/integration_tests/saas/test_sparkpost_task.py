import pytest

from fides.api.ops.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestSparkpostConnector:
    def test_connection(self, sparkpost_runner: ConnectorRunner):
        sparkpost_runner.test_connection()

    async def test_access_request(
        self, sparkpost_runner: ConnectorRunner, policy, sparkpost_identity_email: str
    ):
        access_results = await sparkpost_runner.access_request(
            access_policy=policy, identities={"email": sparkpost_identity_email}
        )

        # verify we only returned data for our identity email

        for recipient in access_results["sparkpost_instance:recipient"]:
            assert recipient["address"]["email"] == sparkpost_identity_email

    # async def test_strict_erasure_request(
    #     self,
    #     sparkpost_runner: ConnectorRunner,
    #     policy: Policy,
    #     erasure_policy_string_rewrite: Policy,
    #     sparkpost_erasure_identity_email: str,
    #     sparkpost_erasure_data,
    #     sparkpost_client
    # ):
    #     (
    #         access_results,
    #         erasure_results,
    #     ) = await sparkpost_runner.strict_erasure_request(
    #         access_policy=policy,
    #         erasure_policy=erasure_policy_string_rewrite,
    #         identities={"email": sparkpost_erasure_identity_email},
    #     )

    #     assert erasure_results == {
    #         "sparkpost_instance:all_recipients": 0,
    #         "sparkpost_instance:recipient": 0,
    #     }


    async def test_non_strict_erasure_request(
        self,
        sparkpost_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        sparkpost_erasure_identity_email: str,
        sparkpost_erasure_data,
        sparkpost_client,
    ):
        (
            access_results,
            erasure_results,
        ) = await sparkpost_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": sparkpost_erasure_identity_email},
        )

        assert erasure_results == {
            "sparkpost_instance:all_recipients": 0,
            "sparkpost_instance:recipient": 1,
        }

        # response = sparkpost_client.get_user(sparkpost_erasure_identity_email)
        # # Since user is deleted, it won't be available so response is 404
        # assert response.status_code == 404