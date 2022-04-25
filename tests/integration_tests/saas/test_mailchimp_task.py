import pytest
import random

from fidesops.graph.graph import DatasetGraph
from fidesops.models.privacy_request import ExecutionLog, PrivacyRequest
from fidesops.schemas.redis_cache import PrivacyRequestIdentity

from fidesops.task import graph_task
from fidesops.task.graph_task import get_cached_data_for_erasures
from tests.graph.graph_test_util import assert_rows_match, records_matching_fields


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp
def test_mailchimp_access_request_task(
    db,
    policy,
    mailchimp_connection_config,
    mailchimp_dataset_config,
    mailchimp_identity_email,
) -> None:
    """Full access request based on the Mailchimp SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_saas_access_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": mailchimp_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = mailchimp_connection_config.get_saas_config().fides_key
    merged_graph = mailchimp_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [mailchimp_connection_config],
        {"email": mailchimp_identity_email},
    )

    assert_rows_match(
        v[f"{dataset_name}:member"],
        min_size=1,
        keys=[
            "id",
            "list_id",
            "email_address",
            "unique_email_id",
            "web_id",
            "email_type",
            "status",
            "merge_fields",
            "ip_signup",
            "timestamp_signup",
            "ip_opt",
            "timestamp_opt",
            "language",
            "email_client",
            "location",
            "source",
            "tags",
        ],
    )
    assert_rows_match(
        v[f"{dataset_name}:conversations"],
        min_size=2,
        keys=["id", "campaign_id", "list_id", "from_email", "from_label", "subject"],
    )
    assert_rows_match(
        v[f"{dataset_name}:messages"],
        min_size=3,
        keys=[
            "id",
            "conversation_id",
            "from_label",
            "from_email",
            "subject",
            "message",
            "read",
            "timestamp",
        ],
    )

    # links
    assert v[f"{dataset_name}:member"][0]["email_address"] == mailchimp_identity_email

    logs = (
        ExecutionLog.query(db=db)
        .filter(ExecutionLog.privacy_request_id == privacy_request.id)
        .all()
    )

    logs = [log.__dict__ for log in logs]
    assert (
        len(
            records_matching_fields(
                logs, dataset_name=dataset_name, collection_name="member"
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs,
                dataset_name=dataset_name,
                collection_name="conversations",
            )
        )
        > 0
    )
    assert (
        len(
            records_matching_fields(
                logs, dataset_name=dataset_name, collection_name="messages"
            )
        )
        > 0
    )


@pytest.mark.integration_saas
@pytest.mark.integration_mailchimp
def test_mailchimp_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    mailchimp_connection_config,
    mailchimp_dataset_config,
    mailchimp_identity_email,
    reset_mailchimp_data,
) -> None:
    """Full erasure request based on the Mailchimp SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_saas_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": mailchimp_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = mailchimp_connection_config.get_saas_config().fides_key
    merged_graph = mailchimp_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [mailchimp_connection_config],
        {"email": mailchimp_identity_email},
    )

    v = graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [mailchimp_connection_config],
        {"email": mailchimp_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
    )

    logs = (
        ExecutionLog.query(db=db)
        .filter(ExecutionLog.privacy_request_id == privacy_request.id)
        .all()
    )
    logs = [log.__dict__ for log in logs]
    assert (
        len(
            records_matching_fields(
                logs,
                dataset_name=dataset_name,
                collection_name="conversations",
                message="No values were erased since no primary key was defined for this collection",
            )
        )
        == 1
    )
    assert (
        len(
            records_matching_fields(
                logs,
                dataset_name=dataset_name,
                collection_name="messages",
                message="No values were erased since no primary key was defined for this collection",
            )
        )
        == 1
    )
    assert v == {
        f"{dataset_name}:member": 1,
        f"{dataset_name}:conversations": 0,
        f"{dataset_name}:messages": 0,
    }
