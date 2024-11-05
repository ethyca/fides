import pytest
import requests

from fides.api.models.policy import Policy
from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner


#@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
class TestSalesforceConnector:

    def test_connection(self, salesforce_runner: ConnectorRunner) -> None:
        salesforce_runner.test_connection()


    #@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_salesforce_access_request_task_by_email(
        privacy_request,
        dsr_version,
        request,
        salesforce_runner: ConnectorRunner,
        policy: Policy,
        salesforce_identity_email,
    ) -> None:
        """Full access request based on the Salesforce SaaS config"""
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await salesforce_runner.access_request(
            access_policy=policy, identities={"email": salesforce_identity_email}
        )

        dataset_name = "salesforce_instance"


        # verify we only returned data for our identity
        assert access_results[f"{dataset_name}:contacts"][0]["Email"] == salesforce_identity_email

        for case in access_results[f"{dataset_name}:cases"]:
            assert case["ContactEmail"] == salesforce_identity_email

        for lead in access_results[f"{dataset_name}:leads"]:
            assert lead["Email"] == salesforce_identity_email

        for campaign_member in access_results[f"{dataset_name}:campaign_members"]:
            assert campaign_member["Email"] == salesforce_identity_email


    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_salesforce_access_request_task_by_phone_number(
        self,
        dsr_version,
        request,
        privacy_request,
        salesforce_runner: ConnectorRunner,
        policy: Policy,
        salesforce_identity_phone_number,
        salesforce_identity_email,
        db,
    ) -> None:

        """Full access request based on the Salesforce SaaS config"""
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        access_results = await salesforce_runner.access_request(
            access_policy=policy, identities={"phone_number": salesforce_identity_phone_number}
        )

        dataset_name = "salesforce_instance"

        # verify we only returned data for our identity
        for contact in access_results[f"{dataset_name}:contacts"]:
            assert contact["Phone"] == salesforce_identity_phone_number
            assert contact["Email"] == salesforce_identity_email

        for lead in access_results[f"{dataset_name}:leads"]:
            assert lead["Phone"] == salesforce_identity_phone_number
            assert lead["Email"] == salesforce_identity_email

        for campaign_member in access_results[f"{dataset_name}:campaign_members"]:
            assert campaign_member["Phone"] == salesforce_identity_phone_number
            assert campaign_member["Email"] == salesforce_identity_email


    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_salesforce_erasure_request_task(
        self,
        db,
        dsr_version,
        request,
        privacy_request,
        policy: Policy,
        salesforce_runner: ConnectorRunner,
        erasure_policy_string_rewrite_name_and_email,
        salesforce_erasure_identity_email,
        salesforce_create_erasure_data,
    ) -> None:
        """Full erasure request based on the Salesforce SaaS config"""
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        (
            account_id,
            contact_id,
            case_id,
            lead_id,
            campaign_member_id,
        ) = salesforce_create_erasure_data


        (
            _,
            erasure_results,
        ) = await salesforce_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite_name_and_email,
            identities={"email": salesforce_erasure_identity_email},
        )

        dataset_name = "salesforce_instance"


        # verify masking request was issued for endpoints with update actions
        assert erasure_results == {
            f"{dataset_name}:campaign_member_list": 0,
            f"{dataset_name}:campaign_members": 1,
            f"{dataset_name}:case_list": 0,
            f"{dataset_name}:cases": 1,
            f"{dataset_name}:contact_list": 0,
            f"{dataset_name}:contacts": 1,
            f"{dataset_name}:lead_list": 0,
            f"{dataset_name}:leads": 1,
        }

        salesforce_secrets = salesforce_connection_config.secrets
        base_url = f"https://{salesforce_secrets['domain']}"
        headers = {
            "Authorization": f"Bearer {salesforce_secrets['access_token']}",
        }

        # campaign_members
        response = requests.get(
            url=f"{base_url}/services/data/v54.0/sobjects/CampaignMember/{campaign_member_id}",
            headers=headers,
        )
        campaign_member = response.json()
        assert campaign_member["FirstName"] == "MASKED"
        assert campaign_member["LastName"] == "MASKED"

        # cases
        # no name on cases

        # contacts
        response = requests.get(
            url=f"{base_url}/services/data/v54.0/sobjects/Contact/{contact_id}",
            headers=headers,
        )
        contacts = response.json()
        assert contacts["FirstName"] == "MASKED"
        assert contacts["LastName"] == "MASKED"

        # leads
        response = requests.get(
            url=f"{base_url}/services/data/v54.0/sobjects/Lead/{lead_id}",
            headers=headers,
        )
        lead = response.json()
        assert lead["FirstName"] == "MASKED"
        assert lead["LastName"] == "MASKED"
