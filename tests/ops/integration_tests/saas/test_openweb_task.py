import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestOpenWebConnector:
    def test_connection(self, openweb_runner: ConnectorRunner):
        openweb_runner.test_connection()

    async def test_non_strict_erasure_request(
        self,
        openweb_runner: ConnectorRunner,
        policy: Policy,
        openweb_erasure_identity_email,
        erasure_policy_string_rewrite: Policy,
        openweb_create_erasure_data,
    ):
        (
            _,
            erasure_results,
        ) = await openweb_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": openweb_erasure_identity_email},
        )

        assert erasure_results == {
            "openweb_instance:user": 1,
            "openweb_external_dataset:openweb_external_collection": 0,
        }
