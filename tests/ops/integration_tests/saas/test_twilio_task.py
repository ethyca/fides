import logging
import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.ctl.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()
logger = logging.getLogger(__name__)


@pytest.mark.integration_saas
@pytest.mark.integration_twilio
def test_twilio_connection_test(twilio_connection_config) -> None:
    get_connector(twilio_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_twilio
@pytest.mark.asyncio
async def test_twilio_access_request_task(
    db,
    policy,
    twilio_connection_config,
    twilio_dataset_config,
    twilio_identity_email,
    connection_config,
    twilio_postgres_dataset_config,
    twilio_postgres_db,
) -> None:
    """Full access request based on the Twilio SaaS config"""
    privacy_request = PrivacyRequest(
        id=f"test_twilio_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = twilio_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = twilio_connection_config.get_saas_config().fides_key
    merged_graph = twilio_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, twilio_postgres_dataset_config.get_graph()])

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [twilio_connection_config, connection_config],
        {"email": twilio_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:users"],
        min_size=1,
        keys=[
            "is_notifiable",
            "date_updated",
            "is_online",
            "friendly_name",
            "account_sid",
            "url",
            "date_created",
            "role_sid",
            "sid",
            "identity",
            "chat_service_sid",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:user_conversations"],
        min_size=1,
        keys=[
            "notification_level",
            "unique_name",
            "user_sid",
            "friendly_name",
            "conversation_sid",
            "unread_messages_count",
            "created_by",
            "account_sid",
            "last_read_message_index",
            "date_created",
            "timers",
            "url",
            "date_updated",
            "attributes",
            "participant_sid",
            "conversation_state",
            "chat_service_sid",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:conversation_messages"],
        min_size=1,
        keys=[
            "body",
            "index",
            "author",
            "date_updated",
            "media",
            "participant_sid",
            "conversation_sid",
            "account_sid",
            "delivery",
            "url",
            "date_created",
            "sid",
            "attributes",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:conversation_participants"],
        min_size=1,
        keys=[
            "last_read_message_index",
            "date_updated",
            "last_read_timestamp",
            "conversation_sid",
            "account_sid",
            "url",
            "date_created",
            "role_sid",
            "sid",
            "attributes",
            "identity",
            "messaging_binding",
        ],
    )



@pytest.mark.integration_saas
@pytest.mark.integration_twilio
@pytest.mark.asyncio
async def test_twilio_erasure_request_task(
    db,
    policy,
    twilio_connection_config,
    twilio_dataset_config,
    twilio_identity_email,
    connection_config,
    twilio_postgres_dataset_config,
    twilio_postgres_db,
    erasure_policy_string_rewrite,
    twilio_erasure_identity_email,
    twilio_erasure_data,
    # twilio_test_client,
) -> None:
    """Full erasure request based on the Twilio SaaS config"""


    privacy_request = PrivacyRequest(
        id=f"test_twilio_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = twilio_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = twilio_connection_config.get_saas_config().fides_key
    merged_graph = twilio_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, twilio_postgres_dataset_config.get_graph()])

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [twilio_connection_config, connection_config],
        {"email": twilio_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:users"],
        min_size=1,
        keys=[
            "is_notifiable",
            "date_updated",
            "is_online",
            "friendly_name",
            "account_sid",
            "url",
            "date_created",
            "role_sid",
            "sid",
            "identity",
            "chat_service_sid",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:user_conversations"],
        min_size=1,
        keys=[
            "notification_level",
            "unique_name",
            "user_sid",
            "friendly_name",
            "conversation_sid",
            "unread_messages_count",
            "created_by",
            "account_sid",
            "last_read_message_index",
            "date_created",
            "timers",
            "url",
            "date_updated",
            "attributes",
            "participant_sid",
            "conversation_state",
            "chat_service_sid",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:conversation_messages"],
        min_size=1,
        keys=[
            "body",
            "index",
            "author",
            "date_updated",
            "media",
            "participant_sid",
            "conversation_sid",
            "account_sid",
            "delivery",
            "url",
            "date_created",
            "sid",
            "attributes",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:conversation_participants"],
        min_size=1,
        keys=[
            "last_read_message_index",
            "date_updated",
            "last_read_timestamp",
            "conversation_sid",
            "account_sid",
            "url",
            "date_created",
            "role_sid",
            "sid",
            "attributes",
            "identity",
            "messaging_binding",
        ],
    )
    temp_masking = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [twilio_connection_config],
        identity_kwargs,
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    # verify masking request was issued for endpoints with delete actions
    # assert x == {
    #     f"{dataset_name}:projects": 0,
    #     f"{dataset_name}:project_access_tokens": 0,
    #     f"{dataset_name}:instances": 0,
    #     f"{dataset_name}:people": 1,
    # }

    CONFIG.execution.masking_strict = temp_masking
