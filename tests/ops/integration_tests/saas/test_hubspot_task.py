import pytest

from fides.api.models.policy import Policy
from tests.fixtures.saas.hubspot_fixtures import HubspotTestClient, user_exists
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner
from tests.ops.test_helpers.saas_test_utils import poll_for_existence

@pytest.mark.skip("Flaky Test - to be investigated in https://ethyca.atlassian.net/browse/LJ-425")
@pytest.mark.integration_saas
class TestHubspotConnector:

    def test_hubspot_connection_test(self, hubspot_runner: ConnectorRunner) -> None:
        hubspot_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_hubspot_access_request_task(
        self,
        hubspot_runner: ConnectorRunner,
        dsr_version,
        request,
        policy: Policy,
        hubspot_identity_email,
        hubspot_data,
    ) -> None:
        """Full access request based on the Hubspot SaaS config"""
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        dataset_name = hubspot_runner.dataset_config.fides_key

        access_results = await hubspot_runner.access_request(
            access_policy=policy, identities={"email": hubspot_identity_email}
        )

        assert len(access_results[f"{dataset_name}:users"]) == 1

        assert (
            access_results[f"{dataset_name}:subscription_preferences"][0]["recipient"]
            == hubspot_identity_email
        )
        assert (
            access_results[f"{dataset_name}:users"][0]["email"]
            == hubspot_identity_email
        )
        assert (
            access_results[f"{dataset_name}:owners"][0]["email"]
            == hubspot_identity_email
        )

    async def test_hubspot_erasure_request_task(
        self,
        hubspot_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite_name_and_email,
        hubspot_identity_email,
        hubspot_data,
        hubspot_test_client: HubspotTestClient,
    ) -> None:
        """Full erasure request based on the Hubspot SaaS config"""

        contact_id, user_id = hubspot_data

        email_subscription_response = hubspot_test_client.get_email_subscriptions(
            email=hubspot_identity_email
        )
        subscription_body = email_subscription_response.json()
        for subscription_status in subscription_body["results"]:
            assert subscription_status["status"] == "SUBSCRIBED"

        (
            _,
            erasure_results,
        ) = await hubspot_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite_name_and_email,
            identities={"email": hubspot_identity_email},
        )

        # Masking request only issued to "contacts", "subscription_preferences", and "users" endpoints
        assert erasure_results == {
            "hubspot_instance:contacts": 1,
            "hubspot_instance:subscription_preferences": 1,
            "hubspot_instance:owners": 0,
            "hubspot_instance:users": 1,
        }

        # Verify the user has been assigned to None
        contact_response = hubspot_test_client.get_contact(contact_id=contact_id)
        contact_body = contact_response.json()
        assert contact_body["properties"]["firstname"] == "MASKED"
        assert contact_body["properties"]["email"].endswith("+masked@ethyca.com")

        # verify user is unsubscribed
        email_subscription_response = hubspot_test_client.get_email_subscriptions(
            email=hubspot_identity_email
        )
        subscription_body = email_subscription_response.json()
        for subscription_status in subscription_body["results"]:
            assert subscription_status["status"] == "UNSUBSCRIBED"

        # verify user is deleted
        error_message = f"User with user id {user_id} could not be deleted from Hubspot"
        poll_for_existence(
            user_exists,
            (user_id, hubspot_test_client),
            error_message=error_message,
            existence_desired=False,
        )
