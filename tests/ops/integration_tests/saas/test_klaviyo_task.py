import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestKlaviyoConnector:
    def test_connection(self, klaviyo_runner: ConnectorRunner):
        klaviyo_runner.test_connection()

    async def test_access_request(
        self,
        klaviyo_runner: ConnectorRunner,
        policy: Policy,
        klaviyo_identity_email: str,
    ):
        access_results = await klaviyo_runner.access_request(
            access_policy=policy, identities={"email": klaviyo_identity_email}
        )

        # verify we only returned data for our identity email
        assert (
            access_results["klaviyo_instance:profiles"][0]["attributes"]["email"]
            == klaviyo_identity_email
        )

    async def test_non_strict_erasure_request(
        self,
        klaviyo_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        klaviyo_erasure_identity_email: str,
        klaviyo_erasure_data,
    ):
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

    async def test_new_consent_request(
        self,
        klaviyo_runner: ConnectorRunner,
        consent_policy: Policy,
        klaviyo_erasure_identity_email,
    ):
        consent_results = await klaviyo_runner.new_consent_request(
            consent_policy, {"email": klaviyo_erasure_identity_email}
        )
        assert consent_results == {"opt_in": True, "opt_out": True}
