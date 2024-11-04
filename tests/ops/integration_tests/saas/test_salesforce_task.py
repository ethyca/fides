import pytest
import requests

from fides.api.graph.graph import DatasetGraph
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors import get_connector
from fides.api.task.graph_task import get_cached_data_for_erasures
from fides.config import CONFIG
from tests.conftest import access_runner_tester, erasure_runner_tester
from tests.ops.graph.graph_test_util import assert_rows_match


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
def test_salesforce_connection_test(salesforce_connection_config) -> None:
    get_connector(salesforce_connection_config).test_connection()


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_salesforce_access_request_task_by_email(
    privacy_request,
    dsr_version,
    request,
    policy,
    salesforce_identity_email,
    salesforce_connection_config,
    salesforce_dataset_config,
    db,
) -> None:
    """Full access request based on the Salesforce SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"email": salesforce_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = salesforce_connection_config.get_saas_config().fides_key
    merged_graph = salesforce_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [salesforce_connection_config],
        {"email": salesforce_identity_email},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:contact_list"], min_size=1, keys=["attributes", "Id"]
    )

    assert_rows_match(
        v[f"{dataset_name}:contacts"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "MasterRecordId",
            "AccountId",
            "LastName",
            "FirstName",
            "Salutation",
            "Name",
            "OtherStreet",
            "OtherCity",
            "OtherState",
            "OtherPostalCode",
            "OtherCountry",
            "OtherLatitude",
            "OtherLongitude",
            "OtherGeocodeAccuracy",
            "OtherAddress",
            "MailingStreet",
            "MailingCity",
            "MailingState",
            "MailingPostalCode",
            "MailingCountry",
            "MailingLatitude",
            "MailingLongitude",
            "MailingGeocodeAccuracy",
            "MailingAddress",
            "Phone",
            "Fax",
            "MobilePhone",
            "HomePhone",
            "OtherPhone",
            "AssistantPhone",
            "ReportsToId",
            "Email",
            "Title",
            "Department",
            "AssistantName",
            "LeadSource",
            "Birthdate",
            "Description",
            "OwnerId",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "LastActivityDate",
            "LastCURequestDate",
            "LastCUUpdateDate",
            "LastViewedDate",
            "LastReferencedDate",
            "EmailBouncedReason",
            "EmailBouncedDate",
            "IsEmailBounced",
            "PhotoUrl",
            "Jigsaw",
            "JigsawContactId",
            "CleanStatus",
            "IndividualId",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:case_list"], min_size=1, keys=["attributes", "Id"]
    )

    assert_rows_match(
        v[f"{dataset_name}:cases"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "MasterRecordId",
            "CaseNumber",
            "ContactId",
            "AccountId",
            "AssetId",
            "SourceId",
            "ParentId",
            "SuppliedName",
            "SuppliedEmail",
            "SuppliedPhone",
            "SuppliedCompany",
            "Type",
            "Status",
            "Reason",
            "Origin",
            "Subject",
            "Priority",
            "Description",
            "IsClosed",
            "ClosedDate",
            "IsEscalated",
            "OwnerId",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "ContactPhone",
            "ContactMobile",
            "ContactEmail",
            "ContactFax",
            "Comments",
            "LastViewedDate",
            "LastReferencedDate",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:campaign_member_list"], min_size=1, keys=["attributes", "Id"]
    )

    assert_rows_match(
        v[f"{dataset_name}:campaign_members"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "CampaignId",
            "LeadId",
            "ContactId",
            "Status",
            "HasResponded",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "FirstRespondedDate",
            "Salutation",
            "Name",
            "FirstName",
            "LastName",
            "Title",
            "Street",
            "City",
            "State",
            "PostalCode",
            "Country",
            "Email",
            "Phone",
            "Fax",
            "MobilePhone",
            "Description",
            "DoNotCall",
            "HasOptedOutOfEmail",
            "HasOptedOutOfFax",
            "LeadSource",
            "CompanyOrAccount",
            "Type",
            "LeadOrContactId",
            "LeadOrContactOwnerId",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:lead_list"], min_size=1, keys=["attributes", "Id"]
    )

    assert_rows_match(
        v[f"{dataset_name}:leads"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "MasterRecordId",
            "LastName",
            "FirstName",
            "Salutation",
            "Name",
            "Title",
            "Company",
            "Street",
            "City",
            "State",
            "PostalCode",
            "Country",
            "Latitude",
            "Longitude",
            "GeocodeAccuracy",
            "Address",
            "Phone",
            "MobilePhone",
            "Fax",
            "Email",
            "Website",
            "PhotoUrl",
            "Description",
            "LeadSource",
            "Status",
            "Industry",
            "Rating",
            "AnnualRevenue",
            "NumberOfEmployees",
            "OwnerId",
            "IsConverted",
            "ConvertedDate",
            "ConvertedAccountId",
            "ConvertedContactId",
            "ConvertedOpportunityId",
            "IsUnreadByOwner",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "LastActivityDate",
            "LastViewedDate",
            "LastReferencedDate",
            "Jigsaw",
            "JigsawContactId",
            "CleanStatus",
            "CompanyDunsNumber",
            "DandbCompanyId",
            "EmailBouncedReason",
            "EmailBouncedDate",
            "IndividualId",
        ],
    )

    # verify we only returned data for our identity
    assert v[f"{dataset_name}:contacts"][0]["Email"] == salesforce_identity_email

    for case in v[f"{dataset_name}:cases"]:
        assert case["ContactEmail"] == salesforce_identity_email

    for lead in v[f"{dataset_name}:leads"]:
        assert lead["Email"] == salesforce_identity_email

    for campaign_member in v[f"{dataset_name}:campaign_members"]:
        assert campaign_member["Email"] == salesforce_identity_email


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_salesforce_access_request_task_by_phone_number(
    policy,
    dsr_version,
    request,
    privacy_request,
    salesforce_identity_phone_number,
    salesforce_identity_email,
    salesforce_connection_config,
    salesforce_dataset_config,
    db,
) -> None:
    """Full access request based on the Salesforce SaaS config"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    identity = Identity(**{"phone_number": salesforce_identity_phone_number})
    privacy_request.cache_identity(identity)

    dataset_name = salesforce_connection_config.get_saas_config().fides_key
    merged_graph = salesforce_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [salesforce_connection_config],
        {"phone_number": salesforce_identity_phone_number},
        db,
    )

    assert_rows_match(
        v[f"{dataset_name}:contact_list"], min_size=1, keys=["attributes", "Id"]
    )

    assert_rows_match(
        v[f"{dataset_name}:contacts"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "MasterRecordId",
            "AccountId",
            "LastName",
            "FirstName",
            "Salutation",
            "Name",
            "OtherStreet",
            "OtherCity",
            "OtherState",
            "OtherPostalCode",
            "OtherCountry",
            "OtherLatitude",
            "OtherLongitude",
            "OtherGeocodeAccuracy",
            "OtherAddress",
            "MailingStreet",
            "MailingCity",
            "MailingState",
            "MailingPostalCode",
            "MailingCountry",
            "MailingLatitude",
            "MailingLongitude",
            "MailingGeocodeAccuracy",
            "MailingAddress",
            "Phone",
            "Fax",
            "MobilePhone",
            "HomePhone",
            "OtherPhone",
            "AssistantPhone",
            "ReportsToId",
            "Email",
            "Title",
            "Department",
            "AssistantName",
            "LeadSource",
            "Birthdate",
            "Description",
            "OwnerId",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "LastActivityDate",
            "LastCURequestDate",
            "LastCUUpdateDate",
            "LastViewedDate",
            "LastReferencedDate",
            "EmailBouncedReason",
            "EmailBouncedDate",
            "IsEmailBounced",
            "PhotoUrl",
            "Jigsaw",
            "JigsawContactId",
            "CleanStatus",
            "IndividualId",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:case_list"], min_size=1, keys=["attributes", "Id"]
    )

    assert_rows_match(
        v[f"{dataset_name}:cases"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "MasterRecordId",
            "CaseNumber",
            "ContactId",
            "AccountId",
            "AssetId",
            "SourceId",
            "ParentId",
            "SuppliedName",
            "SuppliedEmail",
            "SuppliedPhone",
            "SuppliedCompany",
            "Type",
            "Status",
            "Reason",
            "Origin",
            "Subject",
            "Priority",
            "Description",
            "IsClosed",
            "ClosedDate",
            "IsEscalated",
            "OwnerId",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "ContactPhone",
            "ContactMobile",
            "ContactEmail",
            "ContactFax",
            "Comments",
            "LastViewedDate",
            "LastReferencedDate",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:campaign_member_list"], min_size=1, keys=["attributes", "Id"]
    )

    assert_rows_match(
        v[f"{dataset_name}:campaign_members"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "CampaignId",
            "LeadId",
            "ContactId",
            "Status",
            "HasResponded",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "FirstRespondedDate",
            "Salutation",
            "Name",
            "FirstName",
            "LastName",
            "Title",
            "Street",
            "City",
            "State",
            "PostalCode",
            "Country",
            "Email",
            "Phone",
            "Fax",
            "MobilePhone",
            "Description",
            "DoNotCall",
            "HasOptedOutOfEmail",
            "HasOptedOutOfFax",
            "LeadSource",
            "CompanyOrAccount",
            "Type",
            "LeadOrContactId",
            "LeadOrContactOwnerId",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:lead_list"], min_size=1, keys=["attributes", "Id"]
    )

    assert_rows_match(
        v[f"{dataset_name}:leads"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "MasterRecordId",
            "LastName",
            "FirstName",
            "Salutation",
            "Name",
            "Title",
            "Company",
            "Street",
            "City",
            "State",
            "PostalCode",
            "Country",
            "Latitude",
            "Longitude",
            "GeocodeAccuracy",
            "Address",
            "Phone",
            "MobilePhone",
            "Fax",
            "Email",
            "Website",
            "PhotoUrl",
            "Description",
            "LeadSource",
            "Status",
            "Industry",
            "Rating",
            "AnnualRevenue",
            "NumberOfEmployees",
            "OwnerId",
            "IsConverted",
            "ConvertedDate",
            "ConvertedAccountId",
            "ConvertedContactId",
            "ConvertedOpportunityId",
            "IsUnreadByOwner",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "LastActivityDate",
            "LastViewedDate",
            "LastReferencedDate",
            "Jigsaw",
            "JigsawContactId",
            "CleanStatus",
            "CompanyDunsNumber",
            "DandbCompanyId",
            "EmailBouncedReason",
            "EmailBouncedDate",
            "IndividualId",
        ],
    )
    # verify we only returned data for our identity
    for contact in v[f"{dataset_name}:contacts"]:
        assert contact["Phone"] == salesforce_identity_phone_number
        assert contact["Email"] == salesforce_identity_email

    for lead in v[f"{dataset_name}:leads"]:
        assert lead["Phone"] == salesforce_identity_phone_number
        assert lead["Email"] == salesforce_identity_email

    for campaign_member in v[f"{dataset_name}:campaign_members"]:
        assert campaign_member["Phone"] == salesforce_identity_phone_number
        assert campaign_member["Email"] == salesforce_identity_email


@pytest.mark.skip(reason="Currently unable to test OAuth2 connectors")
@pytest.mark.integration_saas
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_salesforce_erasure_request_task(
    db,
    dsr_version,
    request,
    privacy_request,
    erasure_policy_string_rewrite,
    salesforce_connection_config,
    salesforce_dataset_config,
    salesforce_erasure_identity_email,
    salesforce_create_erasure_data,
) -> None:
    """Full erasure request based on the Salesforce SaaS config"""
    privacy_request.policy_id = erasure_policy_string_rewrite.id
    privacy_request.save(db)
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    (
        account_id,
        contact_id,
        case_id,
        lead_id,
        campaign_member_id,
    ) = salesforce_create_erasure_data

    identity = Identity(**{"email": salesforce_erasure_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = salesforce_connection_config.get_saas_config().fides_key
    merged_graph = salesforce_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = access_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [salesforce_connection_config],
        {"email": salesforce_erasure_identity_email},
        db,
    )

    # verify staged data is available for erasure
    assert_rows_match(
        v[f"{dataset_name}:contact_list"], min_size=1, keys=["attributes", "Id"]
    )

    assert_rows_match(
        v[f"{dataset_name}:contacts"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "MasterRecordId",
            "AccountId",
            "LastName",
            "FirstName",
            "Salutation",
            "Name",
            "OtherStreet",
            "OtherCity",
            "OtherState",
            "OtherPostalCode",
            "OtherCountry",
            "OtherLatitude",
            "OtherLongitude",
            "OtherGeocodeAccuracy",
            "OtherAddress",
            "MailingStreet",
            "MailingCity",
            "MailingState",
            "MailingPostalCode",
            "MailingCountry",
            "MailingLatitude",
            "MailingLongitude",
            "MailingGeocodeAccuracy",
            "MailingAddress",
            "Phone",
            "Fax",
            "MobilePhone",
            "HomePhone",
            "OtherPhone",
            "AssistantPhone",
            "ReportsToId",
            "Email",
            "Title",
            "Department",
            "AssistantName",
            "LeadSource",
            "Birthdate",
            "Description",
            "OwnerId",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "LastActivityDate",
            "LastCURequestDate",
            "LastCUUpdateDate",
            "LastViewedDate",
            "LastReferencedDate",
            "EmailBouncedReason",
            "EmailBouncedDate",
            "IsEmailBounced",
            "PhotoUrl",
            "Jigsaw",
            "JigsawContactId",
            "CleanStatus",
            "IndividualId",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:case_list"], min_size=1, keys=["attributes", "Id"]
    )

    assert_rows_match(
        v[f"{dataset_name}:cases"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "MasterRecordId",
            "CaseNumber",
            "ContactId",
            "AccountId",
            "AssetId",
            "SourceId",
            "ParentId",
            "SuppliedName",
            "SuppliedEmail",
            "SuppliedPhone",
            "SuppliedCompany",
            "Type",
            "Status",
            "Reason",
            "Origin",
            "Subject",
            "Priority",
            "Description",
            "IsClosed",
            "ClosedDate",
            "IsEscalated",
            "OwnerId",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "ContactPhone",
            "ContactMobile",
            "ContactEmail",
            "ContactFax",
            "Comments",
            "LastViewedDate",
            "LastReferencedDate",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:campaign_member_list"], min_size=1, keys=["attributes", "Id"]
    )

    assert_rows_match(
        v[f"{dataset_name}:campaign_members"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "CampaignId",
            "LeadId",
            "ContactId",
            "Status",
            "HasResponded",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "FirstRespondedDate",
            "Salutation",
            "Name",
            "FirstName",
            "LastName",
            "Title",
            "Street",
            "City",
            "State",
            "PostalCode",
            "Country",
            "Email",
            "Phone",
            "Fax",
            "MobilePhone",
            "Description",
            "DoNotCall",
            "HasOptedOutOfEmail",
            "HasOptedOutOfFax",
            "LeadSource",
            "CompanyOrAccount",
            "Type",
            "LeadOrContactId",
            "LeadOrContactOwnerId",
        ],
    )

    assert_rows_match(
        v[f"{dataset_name}:lead_list"], min_size=1, keys=["attributes", "Id"]
    )

    assert_rows_match(
        v[f"{dataset_name}:leads"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "MasterRecordId",
            "LastName",
            "FirstName",
            "Salutation",
            "Name",
            "Title",
            "Company",
            "Street",
            "City",
            "State",
            "PostalCode",
            "Country",
            "Latitude",
            "Longitude",
            "GeocodeAccuracy",
            "Address",
            "Phone",
            "MobilePhone",
            "Fax",
            "Email",
            "Website",
            "PhotoUrl",
            "Description",
            "LeadSource",
            "Status",
            "Industry",
            "Rating",
            "AnnualRevenue",
            "NumberOfEmployees",
            "OwnerId",
            "IsConverted",
            "ConvertedDate",
            "ConvertedAccountId",
            "ConvertedContactId",
            "ConvertedOpportunityId",
            "IsUnreadByOwner",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "LastActivityDate",
            "LastViewedDate",
            "LastReferencedDate",
            "Jigsaw",
            "JigsawContactId",
            "CleanStatus",
            "CompanyDunsNumber",
            "DandbCompanyId",
            "EmailBouncedReason",
            "EmailBouncedDate",
            "IndividualId",
        ],
    )

    masking_strict = CONFIG.execution.masking_strict
    CONFIG.execution.masking_strict = True

    x = erasure_runner_tester(
        privacy_request,
        erasure_policy_string_rewrite,
        graph,
        [salesforce_connection_config],
        {"email": salesforce_erasure_identity_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
    )

    # verify masking request was issued for endpoints with update actions
    assert x == {
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

    # reset
    CONFIG.execution.masking_strict = masking_strict
