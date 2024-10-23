import pytest
from loguru import logger

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestSegmentRTFOnlyConnection:
    def test_connection(self, segment_rtf_only_runner: ConnectorRunner):
        segment_rtf_only_runner.test_connection()

    async def test_non_strict_erasure_request_with_email(
        self,
        segment_rtf_only_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_complete_mask: Policy,
        segment_rtf_only_erasure_identity_email: str,
    ):
        (
            _,
            erasure_results,
        ) = await segment_rtf_only_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_complete_mask,
            identities={
                "email": segment_rtf_only_erasure_identity_email,
            },
        )

        assert erasure_results == {
            "segment_rtf_only_external_dataset:segment_rtf_only_external_collection": 0,
            "segment_rtf_only_instance:segment_user": 1,
        }
