import random

import pytest
from fidesops.ops.core.config import config
from fidesops.ops.graph.graph import DatasetGraph
from fidesops.ops.models.privacy_request import PrivacyRequest
from fidesops.ops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.ops.service.connectors import get_connector
from fidesops.ops.task import graph_task
from fidesops.ops.task.graph_task import get_cached_data_for_erasures

from tests.ops.fixtures.saas.logi_id_fixtures import user_exists
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.integration_saas
@pytest.mark.integration_saas
def test_logi_id_connection_test(logi_id_connection_config) -> None:
    get_connector(logi_id_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_logi_id
def test_logi_id_access_request_task(
    db,
    policy,
    logi_id_connection_config,
    logi_id_dataset_config,
    logi_id_identity_email,
) -> None:
    """Full access request based on the Logi ID SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_logi_id_access_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": logi_id_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = logi_id_connection_config.get_saas_config().fides_key
    merged_graph = logi_id_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [logi_id_connection_config],
        {"email": logi_id_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:users"],
        min_size=1,
        keys=[
            "id",
            "sub",
            "email",
            "email_verified",
            "phone_number_verified",
            "given_name",
            "firstname",
            "family_name",
            "lastname",
            "zoneinfo",
            "country",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:user_claims"],
        min_size=1,
        keys=[
            "email_verified",
            "phone_number_verified",
            "given_name",
            "family_name",
            "address",
            "email",
            "zoneinfo",
            "id",
            "location",
            "sub",
            "country",
            "firstname",
            "lastname",
            "provider",
            "twoStepVerificationEnabled",
        ],
    )


@pytest.mark.integration_saas
@pytest.mark.integration_logi_id
def test_logi_id_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    logi_id_secrets,
    logi_id_connection_config,
    logi_id_dataset_config,
    logi_id_erasure_identity_email,
    logi_id_erasure_data,
) -> None:
    """Full erasure request based on the Logi ID SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_logi_id_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": logi_id_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = logi_id_connection_config.get_saas_config().fides_key
    merged_graph = logi_id_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [logi_id_connection_config],
        {"email": logi_id_erasure_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:users"],
        min_size=1,
        keys=[
            "id",
            "sub",
            "email",
            "email_verified",
            "phone_number_verified",
            "given_name",
            "firstname",
            "family_name",
            "lastname",
            "zoneinfo",
            "country",
        ],
    )

    temp_masking = config.execution.masking_strict
    config.execution.masking_strict = False  # Allow delete
    erasure = graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [logi_id_connection_config],
        {"email": logi_id_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )
    assert erasure == {
        "logi_id_connector_example:user_claims": 0,
        "logi_id_connector_example:users": 1,
    }

    # Verifying user is deleted
    error_message = f"User with email {logi_id_erasure_identity_email} could not be deleted in Logi ID"
    poll_for_existence(
        user_exists,
        (logi_id_erasure_identity_email, logi_id_secrets),
        error_message=error_message,
        existence_desired=False,
    )

    config.execution.masking_strict = temp_masking
