from typing import Dict
from unittest import mock

import pytest
from httpx import AsyncClient, Client, HTTPStatusError

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.connectors.fides.fides_client import FidesClient
from fides.api.util.errors import FidesError

SAMPLE_TOKEN = "SOME_TOKEN"


class MockResponse:
    """
    A class to mock Fides API responses
    """

    def __init__(self, is_success, json_data):
        self.is_success = is_success
        self.json_data = json_data

    def json(self):
        return self.json_data


@pytest.fixture(scope="function")
def test_fides_client_bad_credentials(
    fides_connector_example_secrets: Dict[str, str],
) -> FidesClient:
    return FidesClient(
        fides_connector_example_secrets["uri"],
        fides_connector_example_secrets["username"],
        "badpassword",
    )


@pytest.mark.unit
class TestFidesClientUnit:
    """
    Unit tests against functionality in the FidesClient class
    """

    @mock.patch(
        "httpx.post",
        side_effect=[
            MockResponse(True, {"token_data": {"access_token": SAMPLE_TOKEN}})
        ],
    )
    def test_authenticated_request(self, mock_login, test_fides_client: FidesClient):
        """
        Assert that authenticated request properly assigns auth token to the request
        and that request object has basic expected properties
        """
        test_fides_client.login()
        request = test_fides_client.authenticated_request("GET", path="/testpath")
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == f"Bearer {SAMPLE_TOKEN}"
        assert request.method == "GET"
        assert request.url == test_fides_client.uri + "/testpath"

        request = test_fides_client.authenticated_request("get", path="/testpath")
        assert request.method == "GET"
        assert request.url == test_fides_client.uri + "/testpath"

        request = test_fides_client.authenticated_request(
            "GET", path="/testpath", headers={"another_header": "header_value"}
        )
        assert request.method == "GET"
        assert request.url == test_fides_client.uri + "/testpath"
        assert len(request.headers) == 7
        assert "another_header" in request.headers
        assert request.headers["another_header"] == "header_value"
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == f"Bearer {SAMPLE_TOKEN}"

        request = test_fides_client.authenticated_request("POST", path="/testpath")
        assert request.method == "POST"
        assert request.url == test_fides_client.uri + "/testpath"

    def test_authenticated_request_not_logged_in(self, test_fides_client: FidesClient):
        """
        Assert that authenticated request helper throws an error if client is not logged in
        """
        with pytest.raises(FidesError) as exc:
            test_fides_client.authenticated_request("GET", path="/testpath")
        assert "No token" in str(exc)

    @mock.patch(
        "httpx.post",
        side_effect=[
            MockResponse(True, {"token_data": {"access_token": SAMPLE_TOKEN}})
        ],
    )
    def test_authenticated_request_parameters(
        self, mock_login, test_fides_client: FidesClient
    ):
        test_fides_client.login()

        # test query params on GET
        request = test_fides_client.authenticated_request(
            "GET",
            path="/testpath",
            query_params={"param1": "value1", "param2": "value2"},
        )
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == f"Bearer {SAMPLE_TOKEN}"
        assert request.method == "GET"
        assert (
            request.url
            == test_fides_client.uri + "/testpath?param1=value1&param2=value2"
        )

        # test form data passed as dict
        request = test_fides_client.authenticated_request(
            "POST",
            path="/testpath",
            query_params={"param1": "value1", "param2": "value2"},
            data={"key1": "value1", "key2": "value2"},
        )
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == f"Bearer {SAMPLE_TOKEN}"
        assert request.method == "POST"
        assert (
            request.url
            == test_fides_client.uri + "/testpath?param1=value1&param2=value2"
        )
        request.read()
        assert request.content == b"key1=value1&key2=value2"

        # test body passed as string literal
        request = test_fides_client.authenticated_request(
            "POST",
            path="/testpath",
            query_params={"param1": "value1", "param2": "value2"},
            data="testbody",
        )
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == f"Bearer {SAMPLE_TOKEN}"
        assert request.method == "POST"
        assert (
            request.url
            == test_fides_client.uri + "/testpath?param1=value1&param2=value2"
        )
        request.read()
        assert request.content == b"testbody"

        # test json body passed as a dict
        request = test_fides_client.authenticated_request(
            "POST",
            path="/testpath",
            query_params={"param1": "value1", "param2": "value2"},
            json={"field1": "value1"},
        )
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == f"Bearer {SAMPLE_TOKEN}"
        assert request.method == "POST"
        assert (
            request.url
            == test_fides_client.uri + "/testpath?param1=value1&param2=value2"
        )
        request.read()
        assert request.content == b'{"field1": "value1"}'

        # test json body passed as a list
        request = test_fides_client.authenticated_request(
            "POST",
            path="/testpath",
            query_params={"param1": "value1", "param2": "value2"},
            json=[{"field1": "value1"}],
        )
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == f"Bearer {SAMPLE_TOKEN}"
        assert request.method == "POST"
        assert (
            request.url
            == test_fides_client.uri + "/testpath?param1=value1&param2=value2"
        )
        request.read()
        assert request.content == b'[{"field1": "value1"}]'

    @pytest.mark.asyncio
    def test_poll_for_completion(
        self,
        db,
        policy,
        authenticated_fides_client: FidesClient,
        async_api_client: AsyncClient,
    ):
        pr = PrivacyRequest.create(
            db=db,
            data={
                "requested_at": None,
                "policy_id": policy.id,
                "status": PrivacyRequestStatus.complete,
            },
        )

        pr_record = authenticated_fides_client.poll_for_request_completion(
            privacy_request_id=pr.id,
            timeout=10,
            interval=1,
            async_client=async_api_client,
        )
        assert pr_record.status == PrivacyRequestStatus.complete.value

    @pytest.mark.asyncio
    def test_poll_for_completion_errored(
        self,
        db,
        policy,
        authenticated_fides_client: FidesClient,
        async_api_client: AsyncClient,
    ):
        pr = PrivacyRequest.create(
            db=db,
            data={
                "requested_at": None,
                "policy_id": policy.id,
                "status": PrivacyRequestStatus.error,
            },
        )
        with pytest.raises(FidesError) as exc:
            authenticated_fides_client.poll_for_request_completion(
                privacy_request_id=pr.id,
                timeout=10,
                interval=1,
                async_client=async_api_client,
            )
        assert "encountered an error" in str(exc)

    @pytest.mark.asyncio
    def test_poll_for_completion_timeout(
        self,
        db,
        policy,
        authenticated_fides_client: FidesClient,
        async_api_client: AsyncClient,
    ):
        pr = PrivacyRequest.create(
            db=db,
            data={
                "requested_at": None,
                "policy_id": policy.id,
                "status": PrivacyRequestStatus.in_processing,
            },
        )
        with pytest.raises(TimeoutError):
            pr_record = authenticated_fides_client.poll_for_request_completion(
                privacy_request_id="p",
                interval=1,
                timeout=1,
                async_client=async_api_client,
            )


@pytest.mark.integration
class TestFidesClientIntegration:
    """
    Integration tests against functionality in the FidesClient class
    that interacts with a running Fides server.

    These tests rely on a Fides client that is configured to
    connect to the main Fides server running in the
    docker compose test environment.

    This is not the most realistic use case, but it can be used to verify
    the core FidesClient functionality, without relying on more than
    one Fides server instance to be running.
    """

    def test_login(self, test_fides_client: FidesClient):
        """Tests login works as expected"""

        # to test login specifically, create a client directly
        # so that we don't call `create_client()`, which performs
        # login as part of initialization
        test_fides_client.login()
        assert test_fides_client.token is not None

    def test_login_bad_credentials(
        self, test_fides_client_bad_credentials: FidesClient
    ):
        """Tests login fails with bad credentials"""

        # to test login specifically, get the client directly
        # so that we don't call `create_client()`, which performs
        # login as part of initialization

        with pytest.raises(HTTPStatusError):
            test_fides_client_bad_credentials.login()
        assert test_fides_client_bad_credentials.token is None

    def test_create_privacy_request(
        self,
        authenticated_fides_client: FidesClient,
        policy,
        db,
        monkeypatch,
        api_client,
    ):
        """
        Test that properly configured fides client can create and execute a valid access privacy request
        Inspired by `test_privacy_request_endpoints.TestCreatePrivacyRequest`
        """
        monkeypatch.setattr(Client, "send", api_client.send)

        pr_id = authenticated_fides_client.create_privacy_request(
            external_id="test_external_id",
            identity={"email": "test@example.com"},
            policy_key=policy.key,
        )
        assert pr_id is not None
        pr: PrivacyRequest = PrivacyRequest.get(db=db, object_id=pr_id)
        assert pr.external_id == "test_external_id"
        assert pr.policy.key == policy.key
        assert pr.status is not None
        pr.delete(db=db)

    def test_request_status_no_privacy_request(
        self, authenticated_fides_client: FidesClient, monkeypatch, api_client
    ):
        """
        Test that request status can be called successfully with no
        privacy request ID specified. This acts as a basic test to
        validate we can successfully hit authenticated endpoints.
        """
        monkeypatch.setattr(Client, "send", api_client.send)
        statuses = authenticated_fides_client.request_status()
        assert len(statuses) == 0

    def test_request_status_privacy_request(
        self, authenticated_fides_client: FidesClient, policy, monkeypatch, api_client
    ):
        monkeypatch.setattr(Client, "send", api_client.send)

        pr_id = authenticated_fides_client.create_privacy_request(
            external_id="test_external_id",
            identity={"email": "test@example.com"},
            policy_key=policy.key,
        )
        assert pr_id is not None
        statuses = authenticated_fides_client.request_status(privacy_request_id=pr_id)
        assert len(statuses) == 1
        # to make this test more robust to any config changes,
        # or environment-specific issues,
        # let's not assume anything about the status here.
        assert statuses[0]["status"] is not None

    def test_retrieve_request_results_nonexistent_request(
        self, authenticated_fides_client: FidesClient, policy
    ):
        """
        Tests that retrieving requests results for a nonexistent request
        properly returns an empty dict.

        At this point, a nonexistent request behaves the same as a
        legitimate request that does not output data. So we use this to
        ensure that these requests are handled well by the client,
        and simply return no data.
        """
        result = authenticated_fides_client.retrieve_request_results(
            "some_nonexistent_request", "some_nonexistent_rule"
        )
        assert result == {}
