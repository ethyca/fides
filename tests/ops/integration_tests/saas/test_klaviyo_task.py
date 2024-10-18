import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner

@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestKlaviyoConnector:
    def test_connection(self, klaviyo_runner: ConnectorRunner):
        klaviyo_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request(
        self,
        dsr_version,
        request,
        klaviyo_runner: ConnectorRunner,
        policy: Policy,
        klaviyo_identity_email: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await klaviyo_runner.access_request(
            access_policy=policy, identities={"email": klaviyo_identity_email}
        )

        # verify we only returned data for our identity email
        assert (
            access_results["klaviyo_instance:profiles"][0]["attributes"]["email"]
            == klaviyo_identity_email
        )

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_non_strict_erasure_request(
        self,
        request,
        dsr_version,
        klaviyo_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        klaviyo_erasure_identity_email: str,
        klaviyo_erasure_data,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        (
            _,
            erasure_results,
        ) = await klaviyo_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": klaviyo_erasure_identity_email},
        )

        assert erasure_results == {
            "klaviyo_instance:profiles": 1,
        }

    async def test_old_consent_request(
        self,
        klaviyo_runner: ConnectorRunner,
        consent_policy: Policy,
        klaviyo_erasure_identity_email,
    ):
        consent_results = await klaviyo_runner.old_consent_request(
            consent_policy, {"email": klaviyo_erasure_identity_email}
        )
        assert consent_results == {"opt_in": True, "opt_out": True}

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_new_consent_request(
        self,
        dsr_version,
        request,
        klaviyo_runner: ConnectorRunner,
        consent_policy: Policy,
        klaviyo_erasure_identity_email,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        consent_results = await klaviyo_runner.new_consent_request(
            consent_policy, {"email": klaviyo_erasure_identity_email}
        )
        assert consent_results == {"opt_in": True, "opt_out": True}
