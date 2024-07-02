import pytest
import requests

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import get_config
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.skip(reason="No active account")
@pytest.mark.integration_saas
def test_gorgias_connection_test(gorgias_connection_config) -> None:
    get_connector(gorgias_connection_config).test_connection()


@pytest.mark.skip(reason="No active account")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_gorgias_access_request_task(
    db,
    policy,
    gorgias_connection_config,
    gorgias_dataset_config,
    gorgias_identity_email,
    privacy_request,
    dsr_version,
    request,
) -> None:
    """Full access request based on the Gorgias SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": gorgias_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = gorgias_connection_config.get_saas_config().fides_key
    merged_graph = gorgias_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [gorgias_connection_config],
        {"email": gorgias_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "id",
            "external_id",
            "active",
            "name",
            "email",
            "firstname",
            "lastname",
            "language",
            "timezone",
            "created_datetime",
            "updated_datetime",
            "meta",
            "data",
            "note",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:tickets"],
        min_size=1,
        keys=[
            "id",
            "uri",
            "external_id",
            "language",
            "status",
            "priority",
            "channel",
            "via",
            "from_agent",
            "customer",
            "assignee_user",
            "assignee_team",
            "subject",
            "meta",
            "tags",
            "is_unread",
            "spam",
            "created_datetime",
            "opened_datetime",
            "last_received_message_datetime",
            "last_message_datetime",
            "updated_datetime",
            "closed_datetime",
            "snooze_datetime",
            "trashed_datetime",
            "integrations",
            "messages_count",
            "excerpt",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:ticket_messages"],
        min_size=1,
        keys=[
            "id",
            "uri",
            "message_id",
            "ticket_id",
            "external_id",
            "public",
            "channel",
            "via",
            "source",
            "sender",
            "integration_id",
            "intents",
            "rule_id",
            "from_agent",
            "receiver",
            "subject",
            "body_text",
            "body_html",
            "stripped_text",
            "stripped_html",
            "stripped_signature",
            "headers",
            "attachments",
            "actions",
            "macros",
            "meta",
            "created_datetime",
            "sent_datetime",
            "failed_datetime",
            "deleted_datetime",
            "opened_datetime",
            "last_sending_error",
            "is_retriable",
        ],
    )

    # verify we only returned data for our identity email
    assert v[f"{dataset_name}:customer"][0]["email"] == gorgias_identity_email
    user_id = v[f"{dataset_name}:customer"][0]["id"]

    for ticket in v[f"{dataset_name}:tickets"]:
        assert ticket["customer"]["id"] == user_id


@pytest.mark.skip(reason="No active account")
@pytest.mark.skip(reason="Pending account resolution")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_gorgias_erasure_request_task(
    db,
    erasure_policy_string_rewrite,
    gorgias_connection_config,
    gorgias_dataset_config,
    gorgias_erasure_identity_email,
    privacy_request,
    request,
    dsr_version,
    gorgias_create_erasure_data,
) -> None:
    """Full erasure request based on the Gorgias SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True

    identity = Identity(**{"email": gorgias_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = gorgias_connection_config.get_saas_config().fides_key
    merged_graph = gorgias_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [gorgias_connection_config],
        {"email": gorgias_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:customer"],
        min_size=1,
        keys=[
            "id",
            "external_id",
            "active",
            "name",
            "email",
            "firstname",
            "lastname",
            "language",
            "timezone",
            "created_datetime",
            "updated_datetime",
            "meta",
            "data",
            "note",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:tickets"],
        min_size=1,
        keys=[
            "id",
            "uri",
            "external_id",
            "language",
            "status",
            "priority",
            "channel",
            "via",
            "from_agent",
            "customer",
            "assignee_user",
            "assignee_team",
            "subject",
            "meta",
            "tags",
            "is_unread",
            "spam",
            "created_datetime",
            "opened_datetime",
            "last_received_message_datetime",
            "last_message_datetime",
            "updated_datetime",
            "closed_datetime",
            "snooze_datetime",
            "trashed_datetime",
            "integrations",
            "messages_count",
            "excerpt",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:ticket_messages"],
        min_size=1,
        keys=[
            "id",
            "uri",
            "message_id",
            "ticket_id",
            "external_id",
            "public",
            "channel",
            "via",
            "source",
            "sender",
            "integration_id",
            "intents",
            "rule_id",
            "from_agent",
            "receiver",
            "subject",
            "body_text",
            "body_html",
            "stripped_text",
            "stripped_html",
            "stripped_signature",
            "headers",
            "attachments",
            "actions",
            "macros",
            "meta",
            "created_datetime",
            "sent_datetime",
            "failed_datetime",
            "deleted_datetime",
            "opened_datetime",
            "last_sending_error",
            "is_retriable",
        ],
    )

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [gorgias_connection_config],
        {"email": gorgias_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:customer": 1,
        f"{dataset_name}:tickets": 1,
        f"{dataset_name}:ticket_messages": 1,
    }

    gorgias_secrets = gorgias_connection_config.secrets
    auth = gorgias_secrets["username"], gorgias_secrets["api_key"]
    base_url = f"https://{gorgias_secrets['domain']}"

    # user
    response = requests.get(
        url=f"{base_url}/api/customers",
        auth=auth,
        params={"email": gorgias_erasure_identity_email},
    )
    assert response.status_code == 200

    CONFIG.execution.masking_strict = masking_strict
