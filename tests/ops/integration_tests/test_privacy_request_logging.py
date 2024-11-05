from typing import Generator
from unittest import mock

import pytest
from requests import Response

from fides.api.common_exceptions import ClientUnsuccessfulException
from fides.api.util.logger_context_utils import ErrorGroup
from fides.common.api.scope_registry import PRIVACY_REQUEST_CREATE
from fides.common.api.v1.urn_registry import PRIVACY_REQUESTS, V1_URL_PREFIX
from fides.config import CONFIG


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestPrivacyRequestLogging:
    """
    This test sets up the necessary connection configs (using the *_runner fixtures)
    to test an access, erasure, and consent connector. It then creates access, erasure,
    and consent privacy requests to verify that the contextualized logs are being
    output correctly for each action type.
    """

    @pytest.fixture
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUESTS

    @pytest.fixture
    def mock_send(self) -> Generator:
        with mock.patch(
            "fides.api.service.connectors.saas.authenticated_client.Session.send"
        ) as mock_send:
            mock_response = Response()
            mock_response.status_code = 401
            mock_send.return_value = mock_response
            yield mock_send

    @pytest.mark.usefixtures("zendesk_runner")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    def test_access_error_logs(
        self,
        dsr_version,
        request,
        mock_send,
        api_client,
        url,
        generate_auth_header,
        policy,
        loguru_caplog,
        provided_identity_value,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        response = api_client.post(
            url,
            headers=generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE]),
            json=[
                {
                    "policy_key": policy.key,
                    "identity": {"email": provided_identity_value},
                }
            ],
        )

        privacy_request = response.json()["succeeded"][0]

        extra = {
            "action_type": "access",
            "system_key": None,
            "connection_key": "zendesk_instance",
            "collection": "user",
            "privacy_request_id": privacy_request["id"],
            "method": "GET",
            "url": "https://ethyca-test.zendesk.com/api/v2/users/search.json?query=test%40email.com",
            "status_code": 401,
            "error_group": ErrorGroup.authentication_error.value,
        }

        assert (
            f"Connector request failed with status code 401. | {str(extra)}"
            in loguru_caplog.text
        )

    @pytest.mark.usefixtures("typeform_runner")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_erasure_error_logs(
        self,
        dsr_version,
        request,
        mock_send,
        api_client,
        url,
        generate_auth_header,
        erasure_policy,
        loguru_caplog,
        typeform_secrets,
        provided_identity_value,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        masking_strict = CONFIG.execution.masking_strict
        CONFIG.execution.masking_strict = False

        response = api_client.post(
            url,
            headers=generate_auth_header(scopes=[PRIVACY_REQUEST_CREATE]),
            json=[
                {
                    "policy_key": erasure_policy.key,
                    "identity": {"email": provided_identity_value},
                }
            ],
        )

        privacy_request = response.json()["succeeded"][0]

        extra = {
            "action_type": "erasure",
            "system_key": None,
            "connection_key": "typeform_instance",
            "collection": "user",
            "privacy_request_id": privacy_request["id"],
            "method": "DELETE",
            "url": f"https://api.typeform.com/rtbf/{typeform_secrets['account_id']}/responses",
            "status_code": 401,
            "error_group": ErrorGroup.authentication_error.value,
        }

        assert (
            f"Connector request failed with status code 401. | {str(extra)}"
            in loguru_caplog.text
        )

        CONFIG.execution.masking_strict = masking_strict

    @pytest.mark.usefixtures("klaviyo_runner")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_consent_error_logs(
        self,
        dsr_version,
        request,
        mock_send,
        klaviyo_runner,
        consent_policy,
        loguru_caplog,
        provided_identity_value,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        if dsr_version == "use_dsr_2_0":
            with pytest.raises(ClientUnsuccessfulException):
                await klaviyo_runner.new_consent_request(
                    consent_policy,
                    {"email": provided_identity_value},
                    privacy_request_id="123",
                )
        else:
            await klaviyo_runner.new_consent_request(
                consent_policy,
                {"email": provided_identity_value},
                privacy_request_id="123",
            )

        extra = {
            "action_type": "consent",
            "system_key": None,
            "connection_key": "klaviyo_instance",
            "collection": "klaviyo_instance",
            "privacy_request_id": "123",
            "method": "POST",
            "url": "https://a.klaviyo.com/api/profile-suppression-bulk-delete-jobs/",
            "status_code": 401,
            "error_group": ErrorGroup.authentication_error.value,
        }

        assert (
            f"Connector request failed with status code 401. | {str(extra)}"
            in loguru_caplog.text
        )
