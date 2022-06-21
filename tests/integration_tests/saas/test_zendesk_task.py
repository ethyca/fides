import random

import pytest

from fidesops.graph.graph import DatasetGraph
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.task import graph_task
from tests.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
@pytest.mark.integration_zendesk
def test_zendesk_access_request_task(
    db,
    policy,
    zendesk_connection_config,
    zendesk_dataset_config,
    zendesk_identity_email,
) -> None:
    """Full access request based on the Zendesk SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_zendesk_access_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": zendesk_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = zendesk_connection_config.get_saas_config().fides_key
    merged_graph = zendesk_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [zendesk_connection_config],
        {"email": zendesk_identity_email},
    )

    assert_rows_match(
        v[f"{dataset_name}:users"],
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
        v[f"{dataset_name}:user_identities"],
        min_size=1,
        keys=[
            "url",
            "id",
            "user_id",
            "type",
            "value",
            "verified",
            "primary",
            "created_at",
            "undeliverable_count",
            "deliverable_state",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:tickets"],
        min_size=2,
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
            "fields",
            "followup_ids",
            "brand_id",
            "allow_channelback",
            "allow_attachments",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:ticket_comments"],
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
    assert v[f"{dataset_name}:users"][0]["email"] == zendesk_identity_email
    user_id = v[f"{dataset_name}:users"][0]["id"]

    assert v[f"{dataset_name}:user_identities"][0]["value"] == zendesk_identity_email

    for ticket in v[f"{dataset_name}:tickets"]:
        assert ticket["requester_id"] == user_id

    for ticket_comment in v[f"{dataset_name}:ticket_comments"]:
        assert ticket_comment["author_id"] == user_id
