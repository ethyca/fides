import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestGladlyConnection:
    def test_connection(self, gladly_runner: ConnectorRunner):
        gladly_runner.test_connection()

    async def test_non_strict_erasure_request_with_email(
        self,
        gladly_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        gladly_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results,
        ) = await gladly_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={
                "email": gladly_erasure_identity_email,
            },
        )
        assert erasure_results == {"gladly_instance:user": 1}

    async def test_non_strict_erasure_request_with_phone_number(
        self,
        gladly_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        gladly_erasure_identity_phone_number: str,
    ):
        (
            _,
            erasure_results,
        ) = await gladly_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={
                "phone_number": gladly_erasure_identity_phone_number,
            },
        )
        assert erasure_results == {"gladly_instance:user": 1}
