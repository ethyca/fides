import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestTalkableConnector:
    def test_connection(self, talkable_runner: ConnectorRunner):
        talkable_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request(
        self,
        talkable_runner: ConnectorRunner,
        policy,
        request,
        dsr_version,
        talkable_identity_email: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await talkable_runner.access_request(
            access_policy=policy, identities={"email": talkable_identity_email}
        )

        # verify we only returned data for our identity email
        assert (
            access_results["talkable_instance:person"][0]["email"]
            == talkable_identity_email
        )

    @pytest.mark.skip(reason="Temporarily disabled test")
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_non_strict_erasure_request(
        self,
        talkable_runner: ConnectorRunner,
        policy: Policy,
        request,
        dsr_version,
        erasure_policy_string_rewrite: Policy,
        talkable_erasure_identity_email: str,
        talkable_erasure_data,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        (
            access_results,
            erasure_results,
        ) = await talkable_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": talkable_erasure_identity_email},
        )

        assert erasure_results == {
            "talkable_instance:person": 1,
        }
