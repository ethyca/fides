from time import sleep

import pytest
import requests

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


#@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestShoppifyConnector:


    def test_connection(self, shopify_runner: ConnectorRunner):
        shopify_runner.test_connection()

    async def test_access_request(
        self,
        shopify_runner: ConnectorRunner,
        policy: Policy,
        shopify_identity_email: str,
        shopify_access_data
    ):
        access_results = await shopify_runner.access_request(
            access_policy=policy, identities={"email": shopify_identity_email}
        )
        key = shopify_runner.dataset_config.fides_key

        ## Assert for customers email


        ## Assert for Orders by Customer


        ## Assert for blog article comments
        for comment in access_results[f"{key}:blog_article_comments"]:
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
            f"{key}:blogs": 0,
            f"{key}:customer_orders": 1,
            f"{key}:customer_addresses": 2,
            f"{key}:blog_articles": 0,
            f"{key}:blog_article_comments": 1,
            f"{key}:customer_order_transactions": 0,
        }


        sleep(30)  # wait for the data to settle on Shopify's side

        # Verifying data is actually updated

        shopify_secrets = shopify_runner.connection_config.secrets
        base_url = f"https://{shopify_secrets['domain']}"
        headers = {"X-Shopify-Access-Token": f"{shopify_secrets['access_token']}"}

        ##  Note: For Customer data we are removing it from a DSR Request. It might not be inmediate or settled
        ## Possible better validation: Check for DSR existance
        #TODO: Check the DSR existance using GraphQL API

        # Please note that Shopify doesn't allow comments filtering by email so we are getting comment_id by dataset instead and verifying that it is masked
        comment_id = erasure_results[f"{key}:blog_article_comments"][0]["id"]
        blog_article_comment_response = requests.get(
            url=f"{base_url}/admin/api/2022-07/comments/{comment_id}.json",
            headers=headers,
        )

        assert blog_article_comment_response.status_code  == 404
