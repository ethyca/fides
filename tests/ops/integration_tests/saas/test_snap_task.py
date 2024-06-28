import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner
from fides.config import CONFIG


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
class TestsnapConnector:
    def test_connection(self, snap_runner: ConnectorRunner):
        snap_runner.test_connection()

    # Run erasure with masking_strict = False so both update and delete actions can be used
    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = False

    async def test_non_strict_erasure_request(
        self,
        snap_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        snap_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results,
        ) = await snap_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": snap_erasure_identity_email},
        )
    # reset
    CONFIG.execution.masking_strict = masking_strict
