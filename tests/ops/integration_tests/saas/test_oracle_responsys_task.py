import pytest

from fides.api.models.policy import Policy
from fixtures.saas.oracle_responsys_fixtures import oracle_responsys_identity_email
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="Enterprise account only")
@pytest.mark.integration_saas
class TestOracleResponsysConnector:
    def test_connection(self, oracle_responsys_runner: ConnectorRunner):
        oracle_responsys_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request_by_email(
        self,
        dsr_version,
        request,
        oracle_responsys_runner: ConnectorRunner,
        policy,
        oracle_responsys_identity_email: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await oracle_responsys_runner.access_request(
            access_policy=policy, identities={"email": oracle_responsys_identity_email}
        )
        assert (
            access_results["oracle_responsys_instance:profile_list_recipient"][0][
                "email_address"
            ]
            == oracle_responsys_identity_email
        )

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request_by_phone_number(
        self,
        dsr_version,
        request,
        oracle_responsys_runner: ConnectorRunner,
        policy,
        oracle_responsys_identity_phone_number: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await oracle_responsys_runner.access_request(
            access_policy=policy,
            identities={"phone_number": oracle_responsys_identity_phone_number},
        )
        assert (
            access_results["oracle_responsys_instance:profile_list_recipient"][0][
                "mobile_number"
            ]
            == oracle_responsys_identity_phone_number[1:]
        )

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request_by_email_and_extra_identities(
        self,
        dsr_version,
        request,
        oracle_responsys_runner: ConnectorRunner,
        policy,
        oracle_responsys_identity_email: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await oracle_responsys_runner.access_request(
            access_policy=policy,
            identities={
                "email": oracle_responsys_identity_email,
                "extra_identity": "extra_value",
            },
        )
        assert (
            access_results["oracle_responsys_instance:profile_list_recipient"][0][
                "email_address"
            ]
            == oracle_responsys_identity_email
        )

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_non_strict_erasure_request_by_email(
        self,
        dsr_version,
        request,
        oracle_responsys_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        oracle_responsys_erasure_identity_email: str,
        oracle_responsys_erasure_data,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        (
            access_results,
            erasure_results,
        ) = await oracle_responsys_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": oracle_responsys_erasure_identity_email},
        )
        assert erasure_results == {
            "oracle_responsys_instance:profile_list_recipient": 1,
            "oracle_responsys_instance:profile_list": 0,
            "oracle_responsys_instance:profile_extension": 0,
            "oracle_responsys_instance:profile_extension_recipient": 0,
        }

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_non_strict_erasure_request_by_phone_number(
        self,
        dsr_version,
        request,
        oracle_responsys_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        oracle_responsys_erasure_identity_phone_number: str,
        oracle_responsys_erasure_data,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        (
            access_results,
            erasure_results,
        ) = await oracle_responsys_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"phone_number": oracle_responsys_erasure_identity_phone_number},
        )
        assert erasure_results == {
            "oracle_responsys_instance:profile_list_recipient": 1,
            "oracle_responsys_instance:profile_list": 0,
            "oracle_responsys_instance:profile_extension": 0,
            "oracle_responsys_instance:profile_extension_recipient": 0,
        }

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_non_strict_erasure_request_by_multiple_identities(
        self,
        dsr_version,
        request,
        oracle_responsys_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        oracle_responsys_identity_email: str,
        oracle_responsys_erasure_identity_phone_number: str,
        oracle_responsys_erasure_data,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        (
            _,
            erasure_results,
        ) = await oracle_responsys_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={
                "email": oracle_responsys_identity_email,
                "phone_number": oracle_responsys_erasure_identity_phone_number,
            },
            skip_access_results_check=True,
        )
        assert erasure_results == {
            "oracle_responsys_instance:profile_list_recipient": 1,
            "oracle_responsys_instance:profile_list": 0,
            "oracle_responsys_instance:profile_extension_recipient": 0,
        }
