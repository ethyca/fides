import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestTypeformConnector:
    def test_connection(self, typeform_runner: ConnectorRunner):
        typeform_runner.test_connection()

    async def test_non_strict_erasure_request(
        self,
        typeform_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        typeform_erasure_identity_email: str,
    ):
        (erasure_results,) = await typeform_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": typeform_erasure_identity_email},
        )
        assert erasure_results == {"typeform_instance:user": 1}
