import random

import pytest
from firebase_admin import auth
from firebase_admin.auth import UserNotFoundError, UserRecord

from fidesops.ops.graph.graph import DatasetGraph
from fidesops.ops.models.privacy_request import PrivacyRequest
from fidesops.ops.schemas.redis_cache import Identity
from fidesops.ops.service.saas_request.override_implementations.firebase_auth_request_overrides import (
    firebase_auth_user_delete,
    initialize_firebase,
)
from fidesops.ops.task import graph_task
from fidesops.ops.task.graph_task import get_cached_data_for_erasures
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
@pytest.mark.integration_saas_override
@pytest.mark.asyncio
async def test_firebase_auth_access_request(
    db,
    policy,
    firebase_auth_connection_config,
    firebase_auth_dataset_config,
    firebase_auth_user: auth.ImportUserRecord,
) -> None:
    """Full access request based on the Firebase Auth SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_firebase_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": firebase_auth_user.email})
    privacy_request.cache_identity(identity)

    dataset_name = firebase_auth_connection_config.get_saas_config().fides_key
    merged_graph = firebase_auth_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [firebase_auth_connection_config],
        {"email": firebase_auth_user.email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=1,
        keys=[
            "uid",
            "email",
            "display_name",
            "photo_url",
            "disabled",
            "email_verified",
        ],
    )
    response_user = v[f"{dataset_name}:user"][0]
    assert response_user["uid"] == firebase_auth_user.uid
    assert response_user["email"] == firebase_auth_user.email
    assert response_user["display_name"] == firebase_auth_user.display_name
    assert response_user["photo_url"] == firebase_auth_user.photo_url
    assert response_user["disabled"] == firebase_auth_user.disabled
    assert response_user["email_verified"] == firebase_auth_user.email_verified
    assert "phone_number" not in response_user.keys()

    provider_data = response_user["provider_data"]
    assert (
        provider_data[0]["provider_id"]
        == firebase_auth_user.provider_data[0].provider_id
    )
    assert (
        provider_data[0]["display_name"]
        == firebase_auth_user.provider_data[0].display_name
    )
    assert provider_data[0]["email"] == firebase_auth_user.provider_data[0].email
    assert (
        provider_data[0]["photo_url"] == firebase_auth_user.provider_data[0].photo_url
    )
    assert (
        provider_data[1]["provider_id"]
        == firebase_auth_user.provider_data[1].provider_id
    )
    assert (
        provider_data[1]["display_name"]
        == firebase_auth_user.provider_data[1].display_name
    )
    assert provider_data[1]["email"] == firebase_auth_user.provider_data[1].email
    assert "photo_url" not in provider_data[1].keys()


@pytest.mark.integration_saas
@pytest.mark.integration_saas_override
@pytest.mark.asyncio
async def test_firebase_auth_update_request(
    db,
    policy,
    firebase_auth_connection_config,
    firebase_auth_dataset_config,
    firebase_auth_user: auth.ImportUserRecord,
    erasure_policy_string_rewrite,
    firebase_auth_secrets,
) -> None:
    """Update request based on the Firebase Auth SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_firebase_update_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": firebase_auth_user.email})
    privacy_request.cache_identity(identity)

    dataset_name = firebase_auth_connection_config.get_saas_config().fides_key
    merged_graph = firebase_auth_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [firebase_auth_connection_config],
        {"email": firebase_auth_user.email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=1,
        keys=[
            "uid",
            "email",
            "display_name",
            "disabled",
            "email_verified",
        ],
    )

    v = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [firebase_auth_connection_config],
        {"email": firebase_auth_user.email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    app = initialize_firebase(firebase_auth_secrets)
    user: UserRecord = auth.get_user(firebase_auth_user.uid, app=app)
    assert user.display_name == "MASKED"
    assert user.email == firebase_auth_user.email
    assert user.photo_url == firebase_auth_user.photo_url
    assert user.disabled == firebase_auth_user.disabled
    assert user.email_verified == firebase_auth_user.email_verified

    assert (
        user.provider_data[0].provider_id
        == firebase_auth_user.provider_data[0].provider_id
    )
    assert (
        user.provider_data[0].display_name
        == firebase_auth_user.provider_data[0].display_name
    )
    assert user.provider_data[0].email == firebase_auth_user.provider_data[0].email
    assert (
        user.provider_data[0].photo_url == firebase_auth_user.provider_data[0].photo_url
    )
    assert (
        user.provider_data[1].provider_id
        == firebase_auth_user.provider_data[1].provider_id
    )
    assert (
        user.provider_data[1].display_name
        == firebase_auth_user.provider_data[1].display_name
    )
    assert user.provider_data[1].email == firebase_auth_user.provider_data[1].email
    assert (
        user.provider_data[1].photo_url == firebase_auth_user.provider_data[1].photo_url
    )


@pytest.mark.integration_saas
@pytest.mark.integration_saas_override
@pytest.mark.asyncio
async def test_firebase_auth_delete_request(
    db,
    policy,
    firebase_auth_connection_config,
    firebase_auth_dataset_config,
    firebase_auth_user: auth.UserRecord,
    erasure_policy_string_rewrite,
    firebase_auth_secrets,
) -> None:
    """
    Tests delete functionality by explicitly invoking the delete override function

    We can't have an'end-to-end' privacy request test, as preferred, because
    our delete function is not configured by default (the udpate function is).
    But this at least gives us some test coverage of the delete function directly.
    """
    param_values_per_row = [{"email": firebase_auth_user.email}]
    app = initialize_firebase(firebase_auth_secrets)

    # assert user exists
    user_record: UserRecord = auth.get_user_by_email(firebase_auth_user.email, app=app)
    assert user_record.email == firebase_auth_user.email
    assert user_record.uid == firebase_auth_user.uid

    # run the delete function
    firebase_auth_user_delete(param_values_per_row, None, None, firebase_auth_secrets)

    # confirm the user no longer exists
    with pytest.raises(UserNotFoundError):
        auth.get_user_by_email(firebase_auth_user.email, app=app)

    with pytest.raises(UserNotFoundError):
        auth.get_user(firebase_auth_user.uid, app=app)
