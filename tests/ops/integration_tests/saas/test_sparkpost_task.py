import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestSparkPostConnector:
    def test_connection(self, sparkpost_runner: ConnectorRunner):
        sparkpost_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request(
        self,
        sparkpost_runner: ConnectorRunner,
        policy,
        dsr_version,
        request,
        sparkpost_identity_email: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await sparkpost_runner.access_request(
            access_policy=policy, identities={"email": sparkpost_identity_email}
        )
        assert (
            access_results["sparkpost_instance:recipient"][0]["address"]["email"]
            == sparkpost_identity_email
        )

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_non_strict_erasure_request(
        self,
        dsr_version,
        request,
        sparkpost_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        sparkpost_erasure_identity_email: str,
        sparkpost_erasure_data,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        (
            access_results,
            erasure_results,
        ) = await sparkpost_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": sparkpost_erasure_identity_email},
        )
        assert (
            access_results["sparkpost_instance:recipient"][0]["address"]["email"]
            == sparkpost_erasure_identity_email
        )

        assert erasure_results == {
            "sparkpost_instance:recipient_list": 0,
            "sparkpost_instance:recipient": 1,
        }
