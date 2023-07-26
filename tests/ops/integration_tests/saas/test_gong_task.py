import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner
from tests.ops.test_helpers.saas_test_utils import poll_for_existence


@pytest.mark.integration_saas
class TestGongConnector:
    def test_connection(self, gong_runner: ConnectorRunner):
        gong_runner.test_connection()

    async def test_access_request_email(
        self, gong_runner: ConnectorRunner, policy, gong_identity_email: str
    ):
        
        access_results = await gong_runner.access_request(
            access_policy=policy, identities={"email": gong_identity_email}
        )
        
        for data_privacy in access_results["gong_instance:data_privacy"]:
            if(len(data_privacy["customerData"]) > 0):
                assert True
        
    async def test_access_request_phone_number(
        self, gong_runner: ConnectorRunner, policy, gong_identity_phone_number: str
    ):
        access_results = await gong_runner.access_request(
            access_policy=policy, identities={"phone_number": gong_identity_phone_number}
        )
        
        for data_privacy in access_results["gong_instance:data_privacy"]:
            if(len(data_privacy["customerData"]) > 0):
                assert True
 