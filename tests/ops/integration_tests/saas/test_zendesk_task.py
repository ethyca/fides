import pytest
import requests

from fides.api.ops.models.policy import Policy
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestZendeskConnector:
    def test_connection(self, zendesk_runner: ConnectorRunner):
        zendesk_runner.test_connection()

    async def test_access_request(
        self, zendesk_runner: ConnectorRunner, policy, zendesk_identity_email: str
    ):
        access_results = await zendesk_runner.access_request(
            access_policy=policy, identities={"email": zendesk_identity_email}
        )

        assert_rows_match(
            access_results["zendesk_instance:users"],
            min_size=1,
            keys=[
                "id",
                "url",
                "name",
                "email",
                "created_at",
                "updated_at",
                "time_zone",
                "iana_time_zone",
                "phone",
                "shared_phone_number",
                "photo",
                "locale_id",
                "locale",
                "organization_id",
                "role",
                "verified",
                "external_id",
                "tags",
                "alias",
                "active",
                "shared",
                "shared_agent",
                "last_login_at",
                "two_factor_auth_enabled",
                "signature",
                "details",
                "notes",
                "role_type",
                "custom_role_id",
                "moderator",
                "ticket_restriction",
                "only_private_comments",
                "restricted_agent",
                "suspended",
                "default_group_id",
                "report_csv",
            ],
        )

        assert_rows_match(
            access_results["zendesk_instance:user_identities"],
            min_size=2,
            keys=[
                "url",
                "id",
                "user_id",
                "type",
                "value",
                "verified",
                "primary",
                "created_at",
                "updated_at",
            ],
        )

        assert_rows_match(
            access_results["zendesk_instance:tickets"],
            min_size=1,
            keys=[
                "url",
                "id",
                "external_id",
                "via",
                "created_at",
                "updated_at",
                "type",
                "subject",
                "raw_subject",
                "description",
                "priority",
                "status",
                "recipient",
                "requester_id",
                "submitter_id",
                "assignee_id",
                "organization_id",
                "group_id",
                "collaborator_ids",
                "follower_ids",
                "email_cc_ids",
                "forum_topic_id",
                "problem_id",
                "has_incidents",
                "is_public",
                "due_at",
                "tags",
                "custom_fields",
                "satisfaction_rating",
                "sharing_agreement_ids",
                "followup_ids",
                "brand_id",
                "allow_channelback",
                "allow_attachments",
            ],
        )

        assert_rows_match(
            access_results["zendesk_instance:ticket_comments"],
            min_size=1,
            keys=[
                "id",
                "type",
                "author_id",
                "body",
                "html_body",
                "plain_body",
                "public",
                "attachments",
                "audit_id",
                "via",
                "created_at",
                "metadata",
            ],
        )

        # verify we only returned data for our identity email
        assert (
            access_results["zendesk_instance:users"][0]["email"]
            == zendesk_identity_email
        )
        user_id = access_results["zendesk_instance:users"][0]["id"]

        assert (
            access_results["zendesk_instance:user_identities"][0]["value"]
            == zendesk_identity_email
        )

        for ticket in access_results["zendesk_instance:tickets"]:
            assert ticket["requester_id"] == user_id

        for ticket_comment in access_results["zendesk_instance:ticket_comments"]:
            assert ticket_comment["author_id"] == user_id

    async def test_non_strict_erasure_request(
        self,
        zendesk_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        zendesk_erasure_identity_email: str,
        zendesk_erasure_data,
        zendesk_secrets,
    ):
        (
            access_results,
            erasure_results,
        ) = await zendesk_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": zendesk_erasure_identity_email},
        )

        assert erasure_results == {
            "zendesk_instance:users": 1,
            "zendesk_instance:user_identities": 0,
            "zendesk_instance:tickets": 1,
            "zendesk_instance:ticket_comments": 0,
        }

        auth = zendesk_secrets["username"], zendesk_secrets["api_key"]
        base_url = f"https://{zendesk_secrets['domain']}"

        # user
        response = requests.get(
            url=f"{base_url}/v2/users",
            auth=auth,
            params={"email": zendesk_erasure_identity_email},
        )
        # Since user is deleted, it won't be available so response is 404
        assert response.status_code == 404

        for ticket in access_results["zendesk_instance:tickets"]:
            ticket_id = ticket["id"]
            response = requests.get(
                url=f"{base_url}/v2/tickets/{ticket_id}.json",
                auth=auth,
            )
            # Since ticket is deleted, it won't be available so response is 404
            assert response.status_code == 404
