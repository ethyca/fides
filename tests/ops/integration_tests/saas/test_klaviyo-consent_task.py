import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestKlaviyo-ConsentConnector:
    def test_connection(self, klaviyo-consent_runner: ConnectorRunner):
        klaviyo-consent_runner.test_connection()

    async def test_access_request(
        self, klaviyo-consent_runner: ConnectorRunner, policy, klaviyo-consent_identity_email: str
    ):
        access_results = await klaviyo-consent_runner.access_request(
            access_policy=policy, identities={"email": klaviyo-consent_identity_email}
        )

    async def test_strict_erasure_request(
        self,
        klaviyo-consent_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        klaviyo-consent_erasure_identity_email: str,
        klaviyo-consent_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await klaviyo-consent_runner.strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": klaviyo-consent_erasure_identity_email},
        )

    async def test_non_strict_erasure_request(
        self,
        klaviyo-consent_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        klaviyo-consent_erasure_identity_email: str,
        klaviyo-consent_erasure_data,
    ):
        (
            access_results,
            erasure_results,
        ) = await klaviyo-consent_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": klaviyo-consent_erasure_identity_email},
        )