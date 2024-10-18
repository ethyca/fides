import json
from unittest import mock
from unittest.mock import Mock

import pytest
from requests import Response

from fides.api.common_exceptions import FidesopsException
from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestMarigoldEngageConnector:
    def test_connection(self, marigold_engage_runner: ConnectorRunner):
        marigold_engage_runner.test_connection()

    async def test_access_request(
        self,
        marigold_engage_runner: ConnectorRunner,
        policy,
        marigold_engage_identity_email: str,
    ):
        access_results = await marigold_engage_runner.access_request(
            access_policy=policy, identities={"email": marigold_engage_identity_email}
        )
        for user in access_results["marigold_engage_instance:user"]:
            assert user["keys"]["email"] == marigold_engage_identity_email

    async def test_access_request_user_not_found(
        self,
        marigold_engage_runner: ConnectorRunner,
        policy,
    ):
        access_results = await marigold_engage_runner.access_request(
            access_policy=policy,
            identities={"email": "notfound@example.com"},
            skip_collection_verification=True,
        )
        assert access_results == {"marigold_engage_instance:user": []}

    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    async def test_access_request_errored_request(
        self,
        mock_send: Mock,
        marigold_engage_runner: ConnectorRunner,
        policy,
    ):
        response = Response()
        response.status_code = 200
        response._content = json.dumps(
            {
                "errormsg": "Invalid email: notfound@example.com",
                "errorcode": 11,
            }
        ).encode("utf-8")

        mock_send.return_value = response

        with pytest.raises(FidesopsException):
            await marigold_engage_runner.access_request(
                access_policy=policy,
                identities={"email": "notfound@example.com"},
                skip_collection_verification=True,
            )

    async def test_non_strict_erasure_request(
        self,
        marigold_engage_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        marigold_engage_erasure_identity_email: str,
        marigold_engage_erasure_data,
    ):
        (
            _,
            erasure_results,
        ) = await marigold_engage_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": marigold_engage_erasure_identity_email},
        )
        assert erasure_results == {"marigold_engage_instance:user": 1}
