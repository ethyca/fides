import pytest
import requests

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
def test_twilio_conversations_connection_test(
    twilio_conversations_connection_config,
) -> None:
    get_connector(twilio_conversations_connection_config).test_connection()

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_twilio_conversations_access_request_task(
    db,
    policy,
    dsr_version,
    request,
    privacy_request,
    twilio_conversations_connection_config,
    twilio_conversations_dataset_config,
    twilio_conversations_identity_email,
    connection_config,
    twilio_postgres_dataset_config,
    twilio_postgres_db,
) -> None:
    """Full access request based on the Twilio Conversations SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity_attribute = "email"
    identity_value = twilio_conversations_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = twilio_conversations_connection_config.get_saas_config().fides_key
    merged_graph = twilio_conversations_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, twilio_postgres_dataset_config.get_graph()])

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [twilio_conversations_connection_config, connection_config],
        {"email": twilio_conversations_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=1,
        keys=[
            "is_notifiable",
            "date_updated",
            "is_online",
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

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_twilio_conversations_erasure_request_task(
    db,
    dsr_version,
    request,
    privacy_request,
    twilio_conversations_connection_config,
    twilio_conversations_dataset_config,
    connection_config,
    twilio_conversations_postgres_erasure_db,
    twilio_postgres_dataset_config,
    erasure_policy_string_rewrite,
    twilio_conversations_erasure_identity_email,
    twilio_conversations_erasure_identity_name,
    twilio_conversations_erasure_data,
) -> None:
    """Full erasure request based on the Twilio SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)

    identity_attribute = "email"
    identity_value = twilio_conversations_erasure_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = twilio_conversations_connection_config.get_saas_config().fides_key
    merged_graph = twilio_conversations_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, twilio_postgres_dataset_config.get_graph()])

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [twilio_conversations_connection_config, connection_config],
        {"email": twilio_conversations_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
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

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [twilio_conversations_connection_config, connection_config],
        {"email": twilio_conversations_erasure_identity_name},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    # Verify masking request was issued for endpoints with update actions
    assert x == {
        "twilio_conversations_instance:conversation_messages": 1,
        "twilio_conversations_instance:conversation_participants": 0,
        "twilio_conversations_instance:user_conversations": 0,
        "twilio_conversations_instance:user": 1,
        "twilio_postgres:twilio_users": 0,
    }

    # Verifying field is masked
    twilio_conversations_secrets = twilio_conversations_connection_config.secrets

    base_url = f"https://{twilio_conversations_secrets['domain']}"
    auth = (
        twilio_conversations_secrets["account_id"],
        twilio_conversations_secrets["password"],
    )
    user_id = v[f"{dataset_name}:user"][0]["sid"]

    user_response = requests.get(url=f"{base_url}/v1/Users/" + user_id, auth=auth)
    user = user_response.json()
    assert user["friendly_name"] == "MASKED"

    conversations_response = requests.get(
        url=f"{base_url}/v1/Users/" + user_id + "/Conversations", auth=auth
    )

    conversations = conversations_response.json()
    for conversation in conversations["conversations"]:
        conversation_id = conversation["conversation_sid"]
        conversation_messages_response = requests.get(
            url=f"{base_url}/v1/Conversations/" + conversation_id + "/Messages",
            auth=auth,
        )
        messages = conversation_messages_response.json()
        for conversation_message in messages["messages"]:
            assert conversation_message["author"] == "MASKED"

    CONFIG.execution.masking_strict = temp_masking
