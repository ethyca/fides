import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestDoordashConnector:
    def test_connection(self, doordash_runner: ConnectorRunner):
        doordash_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request(
        self,
        dsr_version,
        request,
        doordash_runner: ConnectorRunner,
        policy: Policy,
        doordash_identity_email: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        await doordash_runner.access_request(
            access_policy=policy, identities={"email": doordash_identity_email}
        )
