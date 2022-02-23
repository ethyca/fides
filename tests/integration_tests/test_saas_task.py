import pytest
import random
from fidesops.graph.graph import DatasetGraph
from fidesops.models.privacy_request import ExecutionLog, PrivacyRequest

from fidesops.task import graph_task

from tests.graph.graph_test_util import assert_rows_match, records_matching_fields

@pytest.mark.saas_connector
def test_saas_access_request_task(
    db,
    policy,
    connection_config_saas,
    dataset_config_saas,
    mailchimp_account_email,
) -> None:
    """Full access request based on the Mailchimp SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_saas_access_request_task_{random.randint(0, 1000)}"
    )

    dataset_name = connection_config_saas.get_saas_config().fides_key
    merged_graph = dataset_config_saas.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [connection_config_saas],
        {"email": mailchimp_account_email},
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
        keys=["id", "campaign_id", "list_id"],
    )
    assert_rows_match(
        v[f"{dataset_name}:messages"],
        min_size=7,
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
    assert v[f"{dataset_name}:member"][0]["email_address"] == mailchimp_account_email

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
