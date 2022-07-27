import random
import time

import pytest
import requests

from fidesops.core.config import config
from fidesops.graph.graph import DatasetGraph
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.task import graph_task
from fidesops.task.graph_task import get_cached_data_for_erasures
from tests.ops.graph.graph_test_util import assert_rows_match


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


@pytest.mark.integration_saas
@pytest.mark.integration_zendesk
def test_zendesk_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    zendesk_connection_config,
    zendesk_dataset_config,
    zendesk_erasure_identity_email,
    zendesk_create_erasure_data,
) -> None:
    """Full erasure request based on the zendesk SaaS config"""
    config.execution.masking_strict = False  # Allow Delete

    privacy_request = PrivacyRequest(
        id=f"test_zendesk_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": zendesk_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = zendesk_connection_config.get_saas_config().fides_key
    merged_graph = zendesk_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    # Since we sometimes get response: b'Number of allowed API requests per minute exceeded' so adding this line to avoid it
    time.sleep(60)
    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [zendesk_connection_config],
        {"email": zendesk_erasure_identity_email},
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
        v[f"{dataset_name}:tickets"],
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
            "fields",
            "followup_ids",
            "brand_id",
            "allow_channelback",
            "allow_attachments",
        ],
    )

    x = graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [zendesk_connection_config],
        {"email": zendesk_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
    )

    assert x == {
        f"{dataset_name}:users": 1,
        f"{dataset_name}:user_identities": 0,
        f"{dataset_name}:tickets": 1,
        f"{dataset_name}:ticket_comments": 0,
    }

    zendesk_secrets = zendesk_connection_config.secrets
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

    for ticket in v[f"{dataset_name}:tickets"]:
        ticket_id = ticket["id"]
        response = requests.get(
            url=f"{base_url}/v2/tickets/{ticket_id}.json",
            auth=auth,
        )
        # Since ticket is deleted, it won't be available so response is 404
        assert response.status_code == 404

    config.execution.masking_strict = True
