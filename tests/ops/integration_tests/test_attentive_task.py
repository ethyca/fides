import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="move to plus in progress")
@pytest.mark.integration_saas
class TestAttentiveConnector:
    def test_connection(self, attentive_runner: ConnectorRunner):
        attentive_runner.test_connection()

    async def test_non_strict_erasure_request_with_email(
        self,
        attentive_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        attentive_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results,
        ) = await attentive_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={
                "email": attentive_erasure_identity_email,
            },
        )
        assert erasure_results == {"attentive_instance:user": 1}

    async def test_non_strict_erasure_request_with_phone_number(
        self,
        attentive_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        attentive_erasure_identity_phone_number: str,
    ):
        (
            _,
            erasure_results,
        ) = await attentive_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={
                "phone_number": attentive_erasure_identity_phone_number,
            },
        )
        assert erasure_results == {"attentive_instance:user": 1}
