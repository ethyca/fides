import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
class TestMicrosoftAdvertisingConnector:
    def test_connection(
        self,
        microsoft_advertising_runner: ConnectorRunner,
    ):
        microsoft_advertising_runner.test_connection()

    async def test_non_strict_erasure_request(
        self,
        microsoft_advertising_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        microsoft_advertising_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results,
        ) = await microsoft_advertising_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": microsoft_advertising_erasure_identity_email},
        )
        assert erasure_results == {"microsoft_advertising_instance:user": 1}
