import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="No active account")
@pytest.mark.integration_saas
class TestAlchemerConnector:
    def test_connection(self, alchemer_runner: ConnectorRunner):
        alchemer_runner.test_connection()

    async def test_non_strict_erasure_request(
        self,
        alchemer_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        alchemer_erasure_identity_email: str,
        alchemer_erasure_data,
    ):
        (
            _,
            erasure_results,
        ) = await alchemer_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": alchemer_erasure_identity_email},
        )
        assert erasure_results == {
            "alchemer_instance:user": 1,
        }
