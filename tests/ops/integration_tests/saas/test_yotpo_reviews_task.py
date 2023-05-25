import pytest

from fides.api.models.policy import Policy
from tests.fixtures.saas.yotpo_reviews_fixtures import YotpoReviewsTestClient
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.integration_saas
class TestYotpoReviewsConnector:
    def test_connection(self, yotpo_reviews_runner: ConnectorRunner):
        yotpo_reviews_runner.test_connection()

    async def test_access_request(
        self,
        yotpo_reviews_runner: ConnectorRunner,
        policy,
        yotpo_reviews_identity_email: str,
    ):
        await yotpo_reviews_runner.access_request(
            access_policy=policy, identities={"email": yotpo_reviews_identity_email}
        )

    async def test_strict_erasure_request(
        self,
        yotpo_reviews_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        yotpo_reviews_erasure_data,
        yotpo_reviews_test_client: YotpoReviewsTestClient,
    ):
        email, external_id = yotpo_reviews_erasure_data
        (_, erasure_results) = await yotpo_reviews_runner.strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": email},
        )

        assert erasure_results == {
            "yotpo_reviews_instance:customer": 1,
            "yotpo_reviews_external_dataset:yotpo_reviews_external_collection": 0,
        }

        # get_customer will return None if the first_name has been masked
        poll_for_existence(
            yotpo_reviews_test_client.get_customer,
            (external_id,),
            interval=30,
            existence_desired=False,
        )
