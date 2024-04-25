import pytest

from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
class TestAdobeSignConnector:
    def test_connection(self, adobe_sign_runner: ConnectorRunner):
        adobe_sign_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request(
        self,
        dsr_version,
        request,
        adobe_sign_runner: ConnectorRunner,
        policy,
        adobe_sign_identity_email: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await adobe_sign_runner.access_request(
            access_policy=policy, identities={"email": adobe_sign_identity_email}
        )

        for users in access_results["adobe_sign_instance:users"]:
            assert users["email"] == adobe_sign_identity_email
