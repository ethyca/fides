import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestRecurlyConnector:
    def test_connection(self, recurly_runner: ConnectorRunner):
        recurly_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request(
        self,
        recurly_runner: ConnectorRunner,
        policy,
        dsr_version,
        request,
        recurly_identity_email: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await recurly_runner.access_request(
            access_policy=policy, identities={"email": recurly_identity_email}
        )

        assert len(access_results["recurly_instance:accounts"]) == 1
        account = access_results["recurly_instance:accounts"][0]
        assert account["email"] == recurly_identity_email

        for billing_info in access_results["recurly_instance:billing_info"]:
            assert billing_info["account_id"] == account["id"]

        for shipping_address in access_results["recurly_instance:shipping_address"]:
            assert shipping_address["account_id"] == account["id"]

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_non_strict_erasure_request(
        self,
        request,
        dsr_version,
        recurly_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite_name_and_email: Policy,
        recurly_erasure_identity_email: str,
        recurly_erasure_data,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        (
            access_results,
            erasure_results,
        ) = await recurly_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite_name_and_email,
            identities={"email": recurly_erasure_identity_email},
        )
        assert erasure_results == {
            "recurly_instance:accounts": 1,
            "recurly_instance:billing_info": 1,
            "recurly_instance:shipping_address": 1,
        }
