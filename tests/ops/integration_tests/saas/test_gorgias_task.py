import random
import time

import pytest
import requests

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_gorgias
def test_gorgias_connection_test(gorgias_connection_config) -> None:
    get_connector(gorgias_connection_config).test_connection()

@pytest.mark.integration_saas
@pytest.mark.integration_gorgias
@pytest.mark.asyncio
async def test_gorgias_access_request_task(
    db,
    policy,
    gorgias_connection_config,
    gorgias_dataset_config,
    gorgias_identity_email,
) -> None:
    """Full access request based on the gorgias SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_gorgias_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": gorgias_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = gorgias_connection_config.get_saas_config().fides_key
    merged_graph = gorgias_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
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
        v[f"{dataset_name}:search"],
        min_size=1,
        keys=[
            "data",
            "object",
            "uri",
            "meta",
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
        v[f"{dataset_name}:ticket_message"],
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

    # assert v[f"{dataset_name}:user_identities"][0]["value"] == gorgias_identity_email

    for ticket in v[f"{dataset_name}:tickets"]:
        assert ticket["customer"]['id'] == user_id