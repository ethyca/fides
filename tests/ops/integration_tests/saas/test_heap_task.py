import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.integration_saas
class TestHeapConnector:
    def test_connection(self, heap_runner: ConnectorRunner):
        heap_runner.test_connection()
    
    async def test_non_strict_erasure_request(
        self,
        heap_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        heap_erasure_identity_email: str,
        heap_erasure_data,
        heap_client,
    ):
        
        (
            access_results,
            erasure_results,
        ) = await heap_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": heap_erasure_identity_email},
        )

        assert erasure_results == {
            "heap_instance:auth_token": 0,
            "heap_instance:user": 1
        }

       
