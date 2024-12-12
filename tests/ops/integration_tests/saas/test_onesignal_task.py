import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.skip(reason="Temporarily disabled test")
@pytest.mark.integration_saas
class TestOneSignalConnector:
    def test_connection(self, onesignal_runner: ConnectorRunner):
        onesignal_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request(
        self,
        onesignal_runner: ConnectorRunner,
        policy,
        dsr_version,
        request,
        onesignal_identity_email: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        await onesignal_runner.access_request(
            access_policy=policy, identities={"email": onesignal_identity_email}
        )

    @pytest.mark.usefixtures("use_dsr_3_0")
    async def test_non_strict_erasure_request(
        self,
        onesignal_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        onesignal_erasure_identity_email: str,
        onesignal_erasure_data,
        onesignal_client,
    ):
        """
        Testing this just on one scheduler: DSR 3.0 due to issues with data fixtures not settling down in time,
        {'success': False, 'errors': ['A player with that identifier (XXXXX) already exists. Usually this is caused by calling the same update for multiple player ids. Please double check your update calls and try again']}
        """

        player_id = onesignal_erasure_data
        (
            _,
            erasure_results,
        ) = await onesignal_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": onesignal_erasure_identity_email},
        )

        assert erasure_results == {
            "onesignal_instance:devices": 1,
            "onesignal_external_dataset:onesignal_external_collection": 0,
        }

        poll_for_existence(
            onesignal_client.get_device, (player_id,), existence_desired=False
        )
