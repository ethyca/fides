import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestAppsFlyerConnector:
    def test_connection(self, appsflyer_runner: ConnectorRunner):
        appsflyer_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request(
        self,
        appsflyer_runner: ConnectorRunner,
        policy,
        dsr_version,
        request,
        appsflyer_identity_email: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await appsflyer_runner.access_request(
            access_policy=policy, identities={"email": appsflyer_identity_email}
        )

        assert len(access_results["appsflyer_instance:user"]) == 10

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_non_strict_erasure_request(
        self,
        dsr_version,
        request,
        appsflyer_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        appsflyer_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results,
        ) = await appsflyer_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": appsflyer_erasure_identity_email},
        )
        assert erasure_results == {
            "appsflyer_external_dataset:appsflyer_external_collection": 0,
            "appsflyer_instance:apps": 0,
            "appsflyer_instance:user": 10,
        }
