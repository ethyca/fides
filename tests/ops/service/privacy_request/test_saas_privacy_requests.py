from unittest import mock

import pytest

from fides.api.schemas.masking.masking_configuration import HmacMaskingConfiguration
from fides.api.schemas.saas.saas_config import SaaSRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas_connector import SaaSConnector
from fides.api.service.masking.strategy.masking_strategy_hmac import HmacMaskingStrategy
from tests.ops.service.privacy_request.test_request_runner_service import (
    PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    get_privacy_request_results,
)


@pytest.mark.integration_saas
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_saas_mailchimp(
    trigger_webhook_mock,
    mailchimp_connection_config,
    mailchimp_dataset_config,
    db,
    cache,
    policy,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    dsr_version,
    request,
    mailchimp_identity_email,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = mailchimp_identity_email
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    assert len(results.keys()) == 3

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"mailchimp_instance:"
    member_key = result_key_prefix + "member"
    assert results[member_key][0]["email_address"] == customer_email

    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4

    pr.delete(db=db)


@pytest.mark.integration_saas
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_erasure_request_saas(
    _,
    mailchimp_connection_config,
    mailchimp_dataset_config,
    db,
    cache,
    erasure_policy_hmac,
    generate_auth_header,
    dsr_version,
    request,
    mailchimp_identity_email,
    reset_mailchimp_data,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = mailchimp_identity_email
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": erasure_policy_hmac.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(
        db,
        erasure_policy_hmac,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )

    connector = SaaSConnector(mailchimp_connection_config)
    connector.set_saas_request_state(
        SaaSRequest(path="test_path", method=HTTPMethod.GET)
    )  # dummy request as connector requires it
    request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.GET,
        path="/3.0/search-members",
        query_params={"query": mailchimp_identity_email},
    )
    resp = connector.create_client().send(request)
    body = resp.json()
    merge_fields = body["exact_matches"]["members"][0]["merge_fields"]

    masking_configuration = HmacMaskingConfiguration()
    masking_strategy = HmacMaskingStrategy(masking_configuration)

    assert (
        merge_fields["FNAME"]
        == masking_strategy.mask(
            [reset_mailchimp_data["merge_fields"]["FNAME"]], pr.id
        )[0]
    )
    assert (
        merge_fields["LNAME"]
        == masking_strategy.mask(
            [reset_mailchimp_data["merge_fields"]["LNAME"]], pr.id
        )[0]
    )

    pr.delete(db=db)


@pytest.mark.integration_saas
@mock.patch("fides.api.models.privacy_request.PrivacyRequest.trigger_policy_webhook")
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
def test_create_and_process_access_request_saas_hubspot(
    trigger_webhook_mock,
    connection_config_hubspot,
    dataset_config_hubspot,
    db,
    cache,
    policy,
    policy_pre_execution_webhooks,
    policy_post_execution_webhooks,
    dsr_version,
    request,
    hubspot_identity_email,
    hubspot_data,
    run_privacy_request_task,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    customer_email = hubspot_identity_email
    data = {
        "requested_at": "2021-08-30T16:09:37.359Z",
        "policy_key": policy.key,
        "identity": {"email": customer_email},
    }

    pr = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT_EXTERNAL,
    )
    results = pr.get_raw_access_results()
    assert len(results.keys()) == 4

    for key in results.keys():
        assert results[key] is not None
        assert results[key] != {}

    result_key_prefix = f"hubspot_instance:"
    contacts_key = result_key_prefix + "contacts"
    assert results[contacts_key][0]["properties"]["email"] == customer_email

    # Both pre-execution webhooks and both post-execution webhooks were called
    assert trigger_webhook_mock.call_count == 4

    pr.delete(db=db)
