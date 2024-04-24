import pytest

from fides.api.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


@pytest.mark.skip(reason="No active account")
@pytest.mark.integration_saas
class TestSurveyMonkeyConnector:
    def test_connection(self, surveymonkey_runner: ConnectorRunner):
        surveymonkey_runner.test_connection()

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_request(
        self,
        dsr_version,
        request,
        surveymonkey_runner: ConnectorRunner,
        policy,
        surveymonkey_identity_email: str,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await surveymonkey_runner.access_request(
            access_policy=policy, identities={"email": surveymonkey_identity_email}
        )

        # verify we only returned data for our identity email
        for contacts in access_results["surveymonkey_instance:contacts"]:
            assert contacts["email"] == surveymonkey_identity_email

        for survey_response in access_results["surveymonkey_instance:survey_responses"]:
            assert (
                survey_response["metadata"]["contact"]["email"]["value"]
                == surveymonkey_identity_email
            )

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_non_strict_erasure_request(
        self,
        dsr_version,
        request,
        surveymonkey_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        surveymonkey_erasure_identity_email: str,
        surveymonkey_erasure_data,
        surveymonkey_client,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

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
            "surveymonkey_instance:survey_responses": 1,
        }
