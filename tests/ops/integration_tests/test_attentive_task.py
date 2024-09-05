
import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestAttentiveConnector:
    def test_connection(self, attentive_runner: ConnectorRunner):
        attentive_runner.test_connection()

    async def test_non_strict_erasure_request(
        self,
        attentive_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        attentive_erasure_identity_email: str,
        attentive_erasure_identity_phone_number: str
    ):
        (
            _,
            erasure_results,
        ) = await attentive_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={
                "email": attentive_erasure_identity_email,
                "phone_number": attentive_erasure_identity_phone_number,
            },
        )
        # We set the email to 1 since its 1 request only(?)
        assert erasure_results == {"attentive_instance:delete_request": 1}
