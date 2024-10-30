import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="move to plus in progress")
class TestAdaChatbotConnector:
    def test_connection(self, ada_chatbot_runner: ConnectorRunner):
        ada_chatbot_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_non_strict_erasure_request(
        self,
        ada_chatbot_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        ada_chatbot_erasure_identity_email: str,
        dsr_version,
        request,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        (
            _,
            erasure_results,
        ) = await ada_chatbot_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": ada_chatbot_erasure_identity_email},
        )
        assert erasure_results == {"ada_chatbot_instance:chatter": 1}
