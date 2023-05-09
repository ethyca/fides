import pytest

from fides.api.ops.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.integration_saas
class TestSurveyMonkeyConnector:
    def test_connection(self, surveymonkey_runner: ConnectorRunner):
        surveymonkey_runner.test_connection()

    # async def test_access_request(
    #     self, surveymonkey_runner: ConnectorRunner, policy, surveymonkey_identity_email: str
    # ):
    #     access_results = await surveymonkey_runner.access_request(
    #         access_policy=policy, identities={"email": surveymonkey_identity_email}
    #     )

    #     # verify we only returned data for our identity email

    #     for contacts in access_results["surveymonkey_instance:contacts"]:
    #         assert contacts["email"] == surveymonkey_identity_email

    #     for surveys in access_results["surveymonkey_instance:surveys"]:
    #         assert contacts["email"] == surveymonkey_identity_email

    async def test_non_strict_erasure_request(
        self,
        surveymonkey_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        surveymonkey_erasure_identity_email: str,
        surveymonkey_erasure_data,
        surveymonkey_client,
    ):
        (
            access_results,
            erasure_results,
        ) = await surveymonkey_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": surveymonkey_erasure_identity_email},
        )

        assert erasure_results == {
            "surveymonkey_instance:contacts": 1,
            "surveymonkey_instance:surveys": 0,
            "surveymonkey_instance:collectors": 0,
            "surveymonkey_instance:survey_response": 1,
        }
