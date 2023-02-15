from uuid import uuid4

import pytest
from firebase_admin import auth
from firebase_admin.auth import UserNotFoundError, UserRecord

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.saas_request.override_implementations.firebase_auth_request_overrides import (
    firebase_auth_user_delete,
    initialize_firebase,
)
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_firebase_auth
@pytest.mark.asyncio
async def test_firebase_auth_access_request(
    db,
    policy,
    firebase_auth_connection_config,
    firebase_auth_dataset_config,
    firebase_auth_user: auth.ImportUserRecord,
) -> None:
    """Full access request based on the Firebase Auth SaaS config"""

    privacy_request = PrivacyRequest(id=f"test_firebase_access_request_task_{uuid4()}")
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
            "phone_number",
        ],
    )
    response_user = v[f"{dataset_name}:user"][0]
    assert response_user["uid"] == firebase_auth_user.uid
    assert response_user["email"] == firebase_auth_user.email
    assert response_user["display_name"] == firebase_auth_user.display_name
    assert response_user["phone_number"] == firebase_auth_user.phone_number
    assert response_user["photo_url"] == firebase_auth_user.photo_url
    assert response_user["disabled"] == firebase_auth_user.disabled
    assert response_user["email_verified"] == firebase_auth_user.email_verified

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
@pytest.mark.integration_firebase_auth
@pytest.mark.asyncio
@pytest.mark.usefixtures("firebase_auth_user")
@pytest.mark.parametrize(
    "identity_info, message",
    [
        ({"email": "a_fake_email@ethyca.com"}, "Could not find user with email"),
        ({"phone_number": "+10000000000"}, "Could not find user with phone_number"),
    ],
)
async def test_firebase_auth_access_request_non_existent_users(
    identity_info,
    message,
    db,
    policy,
    firebase_auth_connection_config,
    firebase_auth_dataset_config,
    loguru_caplog,
) -> None:
    """Ensure that firebase access request task gracefully handles non-existent users"""
    privacy_request = PrivacyRequest(id=f"test_firebase_access_request_task_{uuid4()}")
    identity = Identity(**identity_info)
    privacy_request.cache_identity(identity)
    dataset_name = firebase_auth_connection_config.get_saas_config().fides_key
    merged_graph = firebase_auth_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)
    # just ensure we don't error out here
    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [firebase_auth_connection_config],
        identity_info,
        db,
    )
    assert_rows_match(
        v[f"{dataset_name}:user"],
        min_size=0,
        keys=[
            "uid",
            "email",
            "display_name",
            "photo_url",
            "disabled",
            "email_verified",
            "phone_number",
        ],
    )
    # and ensure we've correctly added a warning log
    assert message in loguru_caplog.text


@pytest.mark.integration_saas
@pytest.mark.integration_firebase_auth
@pytest.mark.asyncio
async def test_firebase_auth_access_request_phone_number_identity(
    db,
    policy,
    firebase_auth_connection_config,
    firebase_auth_dataset_config,
    firebase_auth_user: auth.ImportUserRecord,
) -> None:
    """Full access request based on the Firebase Auth SaaS config using a phone number identity"""

    privacy_request = PrivacyRequest(id=f"test_firebase_access_request_task_{uuid4()}")
    identity = Identity(**{"phone_number": firebase_auth_user.phone_number})
    privacy_request.cache_identity(identity)

    dataset_name = firebase_auth_connection_config.get_saas_config().fides_key
    merged_graph = firebase_auth_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [firebase_auth_connection_config],
        {"phone_number": firebase_auth_user.phone_number},
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
            "phone_number",
        ],
    )
    response_user = v[f"{dataset_name}:user"][0]
    assert response_user["uid"] == firebase_auth_user.uid
    assert response_user["email"] == firebase_auth_user.email
    assert response_user["display_name"] == firebase_auth_user.display_name
    assert response_user["phone_number"] == firebase_auth_user.phone_number
    assert response_user["photo_url"] == firebase_auth_user.photo_url
    assert response_user["disabled"] == firebase_auth_user.disabled
    assert response_user["email_verified"] == firebase_auth_user.email_verified

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


@pytest.mark.skip(
    "Re-enable this test if the general config needs to test the user update functionality"
)
@pytest.mark.integration_saas
@pytest.mark.integration_firebase_auth
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

    privacy_request = PrivacyRequest(id=f"test_firebase_update_request_task_{uuid4()}")
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

    await graph_task.run_erasure(
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


@pytest.mark.skip(
    "Re-enable this test if the general config needs to test the user update functionality"
)
@pytest.mark.integration_saas
@pytest.mark.integration_firebase_auth
@pytest.mark.asyncio
async def test_firebase_auth_update_request_phone_number_identity(
    db,
    policy,
    firebase_auth_connection_config,
    firebase_auth_dataset_config,
    firebase_auth_user: auth.ImportUserRecord,
    erasure_policy_string_rewrite,
    firebase_auth_secrets,
) -> None:
    """Update request based on the Firebase Auth SaaS config"""

    privacy_request = PrivacyRequest(id=f"test_firebase_update_request_task_{uuid4()}")
    identity = Identity(**{"phone_number": firebase_auth_user.phone_number})
    privacy_request.cache_identity(identity)

    dataset_name = firebase_auth_connection_config.get_saas_config().fides_key
    merged_graph = firebase_auth_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [firebase_auth_connection_config],
        {"phone_number": firebase_auth_user.phone_number},
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

    await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [firebase_auth_connection_config],
        {"phone_number": firebase_auth_user.phone_number},
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
@pytest.mark.integration_firebase_auth
@pytest.mark.asyncio
async def test_firebase_auth_delete_request(
    db,
    policy,
    firebase_auth_connection_config,
    firebase_auth_dataset_config,
    firebase_auth_user: auth.ImportUserRecord,
    erasure_policy_string_rewrite,
    firebase_auth_secrets,
) -> None:
    """Delete request based on the Firebase Auth SaaS config"""

    privacy_request = PrivacyRequest(id=f"test_firebase_delete_request_task_{uuid4()}")
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

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [firebase_auth_connection_config],
        {"email": firebase_auth_user.email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:user": 1,
    }

    app = initialize_firebase(firebase_auth_secrets)

    # confirm the user no longer exists
    with pytest.raises(UserNotFoundError):
        auth.get_user_by_email(firebase_auth_user.email, app=app)

    with pytest.raises(UserNotFoundError):
        auth.get_user(firebase_auth_user.uid, app=app)

    CONFIG.execution.masking_strict = masking_strict


@pytest.mark.integration_saas
@pytest.mark.integration_firebase_auth
@pytest.mark.asyncio
async def test_firebase_auth_delete_request_phone_number_identity(
    db,
    policy,
    firebase_auth_connection_config,
    firebase_auth_dataset_config,
    firebase_auth_user: auth.ImportUserRecord,
    erasure_policy_string_rewrite,
    firebase_auth_secrets,
) -> None:
    """Delete request based on the Firebase Auth SaaS config"""

    privacy_request = PrivacyRequest(id=f"test_firebase_delete_request_task_{uuid4()}")
    identity = Identity(**{"phone_number": firebase_auth_user.phone_number})
    privacy_request.cache_identity(identity)

    dataset_name = firebase_auth_connection_config.get_saas_config().fides_key
    merged_graph = firebase_auth_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [firebase_auth_connection_config],
        {"phone_number": firebase_auth_user.phone_number},
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

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False

    x = await graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [firebase_auth_connection_config],
        {"phone_number": firebase_auth_user.phone_number},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    assert x == {
        f"{dataset_name}:user": 1,
    }

    app = initialize_firebase(firebase_auth_secrets)

    # confirm the user no longer exists
    with pytest.raises(UserNotFoundError):
        auth.get_user_by_phone_number(firebase_auth_user.phone_number, app=app)

    with pytest.raises(UserNotFoundError):
        auth.get_user(firebase_auth_user.uid, app=app)

    CONFIG.execution.masking_strict = masking_strict


@pytest.mark.integration_saas
@pytest.mark.integration_saas_override
@pytest.mark.asyncio
async def test_firebase_auth_user_delete_function(
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

    We can't have an 'end-to-end' privacy request test, as preferred, because
    our delete function is not configured by default (the update function is).
    But this at least gives us some test coverage of the delete function directly.
    """
    privacy_request = PrivacyRequest(id=f"test_firebase_delete_request_task_{uuid4()}")
    identity = Identity(**{"email": firebase_auth_user.email})
    privacy_request.cache_identity(identity)

    param_values_per_row = [{"email": firebase_auth_user.email}]
    app = initialize_firebase(firebase_auth_secrets)

    # assert user exists
    user_record: UserRecord = auth.get_user_by_email(firebase_auth_user.email, app=app)
    assert user_record.email == firebase_auth_user.email
    assert user_record.uid == firebase_auth_user.uid

    # run the delete function
    firebase_auth_user_delete(
        None, param_values_per_row, None, privacy_request, firebase_auth_secrets
    )

    # confirm the user no longer exists
    with pytest.raises(UserNotFoundError):
        auth.get_user_by_email(firebase_auth_user.email, app=app)

    with pytest.raises(UserNotFoundError):
        auth.get_user(firebase_auth_user.uid, app=app)


@pytest.mark.integration_saas
@pytest.mark.integration_saas_override
@pytest.mark.asyncio
async def test_firebase_auth_user_delete_function_with_phone_number_identity(
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

    We can't have an 'end-to-end' privacy request test, as preferred, because
    our delete function is not configured by default (the update function is).
    But this at least gives us some test coverage of the delete function directly.
    """
    privacy_request = PrivacyRequest(id=f"test_firebase_delete_request_task_{uuid4()}")
    identity = Identity(**{"phone_number": firebase_auth_user.phone_number})
    privacy_request.cache_identity(identity)

    param_values_per_row = [{"phone_number": firebase_auth_user.phone_number}]
    app = initialize_firebase(firebase_auth_secrets)

    # assert user exists
    user_record: UserRecord = auth.get_user_by_phone_number(
        firebase_auth_user.phone_number, app=app
    )
    assert user_record.phone_number == firebase_auth_user.phone_number
    assert user_record.uid == firebase_auth_user.uid

    # run the delete function
    firebase_auth_user_delete(
        None, param_values_per_row, None, privacy_request, firebase_auth_secrets
    )

    # confirm the user no longer exists
    with pytest.raises(UserNotFoundError):
        auth.get_user_by_phone_number(firebase_auth_user.phone_number, app=app)

    with pytest.raises(UserNotFoundError):
        auth.get_user(firebase_auth_user.uid, app=app)
