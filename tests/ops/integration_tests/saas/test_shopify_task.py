import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestShoppifyConnector:

    def test_connection(self, shopify_runner: ConnectorRunner):
        shopify_runner.test_connection()

    async def test_access_request(
        self,
        shopify_runner: ConnectorRunner,
        policy: Policy,
        shopify_identity_email: str,
        shopify_access_data,
    ):
        access_results = await shopify_runner.access_request(
            access_policy=policy, identities={"email": shopify_identity_email}
        )
        key = shopify_runner.dataset_config.fides_key

        ## Assert for customers email
        for customer in access_results[f"{key}:customers"]:
            assert customer["email"] == shopify_identity_email

        ## Assert for Orders by Customer
        orders = access_results[f"{key}:customer_orders"]
        assert len(orders) == len(shopify_access_data["orders"])
        for order in orders:
            assert order["email"] == shopify_identity_email

        ## Assert for blog article comments
        comments = access_results[f"{key}:blog_article_comments"]
        assert len(comments) == len(shopify_access_data["comments"])
        for comment in comments:
            assert comment["author"]["email"] == shopify_identity_email

    async def test_non_strict_erasure_request_with_email(
        self,
        shopify_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        shopify_erasure_identity_email,
        shopify_erasure_data,
    ) -> None:
        """Full erasure request based on the Shopify SaaS config"""
        (
            _,
            erasure_results,
        ) = await shopify_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={
                "email": shopify_erasure_identity_email,
            },
        )
        key = shopify_runner.dataset_config.fides_key

        assert erasure_results == {
            f"{key}:customers": 1,
            f"{key}:customer_orders": 0,
            f"{key}:customer_addresses": 0,
            f"{key}:blog_article_comments": 1,
        }
