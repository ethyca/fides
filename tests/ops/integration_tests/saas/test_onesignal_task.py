import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.integration_saas
class TestOneSignalConnector:
    def test_connection(self, onesignal_runner: ConnectorRunner):
        onesignal_runner.test_connection()

    async def test_access_request(
        self, onesignal_runner: ConnectorRunner, policy, onesignal_identity_email: str
    ):
        access_results = await onesignal_runner.access_request(
            access_policy=policy, identities={"email": onesignal_identity_email}
        )

    async def test_non_strict_erasure_request(
        self,
        onesignal_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        onesignal_erasure_identity_email: str,
        onesignal_erasure_data,
        onesignal_client,
    ):
        player_id = onesignal_erasure_data
        (
            access_results,
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
