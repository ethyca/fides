import random

import pytest

from fidesops.core.config import config
from fidesops.graph.graph import DatasetGraph
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.task import graph_task
from fidesops.task.graph_task import get_cached_data_for_erasures
from tests.ops.fixtures.saas.sendgrid_fixtures import contact_exists
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.integration_saas
@pytest.mark.integration_sendgrid
def test_sendgrid_access_request_task(
    db,
    policy,
    sendgrid_connection_config,
    sendgrid_dataset_config,
    sendgrid_identity_email,
) -> None:
    """Full access request based on the Sendgrid SaaS config"""
    privacy_request = PrivacyRequest(
        id=f"test_saas_access_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": sendgrid_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = sendgrid_connection_config.get_saas_config().fides_key
    merged_graph = sendgrid_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [sendgrid_connection_config],
        {"email": sendgrid_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:contacts"],
        min_size=1,
        keys=[
            "id",
            "first_name",
            "last_name",
            "email",
            "alternate_emails",
            "address_line_1",
            "address_line_2",
            "city",
            "state_province_region",
            "country",
            "postal_code",
            "phone_number",
            "whatsapp",
            "list_ids",
            "segment_ids",
            "created_at",
            "updated_at",
        ],
    )


@pytest.mark.integration_saas
@pytest.mark.integration_sendgrid
def test_sendgrid_erasure_request_task(
    db,
    policy,
    erasure_policy_string_rewrite,
    sendgrid_secrets,
    sendgrid_connection_config,
    sendgrid_dataset_config,
    sendgrid_erasure_identity_email,
    sendgrid_erasure_data,
) -> None:
    """Full erasure request based on the sendgrid SaaS config"""
    privacy_request = PrivacyRequest(
        id=f"test_saas_erasure_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": sendgrid_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = sendgrid_connection_config.get_saas_config().fides_key
    merged_graph = sendgrid_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    # access our erasure identity
    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [sendgrid_connection_config],
        {"email": sendgrid_erasure_identity_email},
        db,
    )

    # make sure erasure contact has expected fields
    assert_rows_match(
        v[f"{dataset_name}:contacts"],
        min_size=1,
        keys=[
            "id",
            "first_name",
            "last_name",
            "email",
            "alternate_emails",
            "address_line_1",
            "address_line_2",
            "city",
            "state_province_region",
            "country",
            "postal_code",
            "phone_number",
            "whatsapp",
            "list_ids",
            "segment_ids",
            "created_at",
            "updated_at",
        ],
    )
    temp_masking = config.execution.masking_strict
    config.execution.masking_strict = False  # Allow delete
    erasure = graph_task.run_erasure(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [sendgrid_connection_config],
        {"email": sendgrid_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )
    assert erasure == {"sendgrid_connector_example:contacts": 1}
    error_message = f"Contact with email {sendgrid_erasure_identity_email} could not be deleted in Sendgrid"
    poll_for_existence(
        contact_exists,
        (sendgrid_erasure_identity_email, sendgrid_secrets),
        error_message=error_message,
        existence_desired=False,
    )

    config.execution.masking_strict = temp_masking
