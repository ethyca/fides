import pytest

from fides.api.common_exceptions import FidesopsException
from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="No active account")
@pytest.mark.integration_saas
class TestZendeskConnector:
    def test_connection(self, zendesk_runner: ConnectorRunner):
        zendesk_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request(
        self,
        dsr_version,
        request,
        zendesk_runner: ConnectorRunner,
        policy: Policy,
        zendesk_identity_email: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await zendesk_runner.access_request(
            access_policy=policy, identities={"email": zendesk_identity_email}
        )

        # verify we only returned data for our identity email
        assert (
            access_results["zendesk_instance:user"][0]["email"]
            == zendesk_identity_email
        )
        user_id = access_results["zendesk_instance:user"][0]["id"]

        assert (
            access_results["zendesk_instance:user_identities"][0]["value"]
            == zendesk_identity_email
        )

        for ticket in access_results["zendesk_instance:tickets"]:
            assert ticket["requester_id"] == user_id

        for ticket_comment in access_results["zendesk_instance:ticket_comments"]:
            assert ticket_comment["author_id"] == user_id

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_non_strict_erasure_request(
        self,
        dsr_version,
        request,
        zendesk_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        zendesk_erasure_identity_email: str,
        zendesk_erasure_data,
        zendesk_client,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        (
            access_results,
            erasure_results,
        ) = await zendesk_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": zendesk_erasure_identity_email},
        )

        assert erasure_results == {
            "zendesk_instance:user": 1,
            "zendesk_instance:user_identities": 0,
            "zendesk_instance:tickets": 1,
            "zendesk_instance:ticket_comments": 0,
        }

        response = zendesk_client.get_user(zendesk_erasure_identity_email)
        # Since user is deleted, it won't be available so response is 404
        assert response.status_code == 404

        for ticket in access_results["zendesk_instance:tickets"]:
            response = zendesk_client.get_ticket(ticket["id"])
            # Since ticket is deleted, it won't be available so response is 404
            assert response.status_code == 404

    async def test_non_strict_erasure_request_fails_with_open_tickets(
        self,
        request,
        zendesk_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        zendesk_erasure_identity_email: str,
        zendesk_erasure_data_with_open_comments,
        zendesk_client,
    ):

        with pytest.raises(
            FidesopsException, match="User still has open tickets, halting request"
        ):
            await zendesk_runner.non_strict_erasure_request(
                access_policy=policy,
                erasure_policy=erasure_policy_string_rewrite,
                identities={"email": zendesk_erasure_identity_email},
            )
