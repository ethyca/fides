import random

import pytest

from fidesops.graph.graph import DatasetGraph
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.service.connectors import get_connector
from fidesops.task import graph_task
from tests.graph.graph_test_util import assert_rows_match


@pytest.mark.integration_saas
@pytest.mark.integration_salesforce
def test_salesforce_connection_test(salesforce_connection_config) -> None:
    get_connector(salesforce_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_salesforce
def test_salesforce_access_request_task(
    policy,
    salesforce_identity_email,
    salesforce_connection_config,
    salesforce_dataset_config,
) -> None:
    """Full access request based on the Salesforce SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_salesforce_access_request_task_{random.randint(0, 1000)}"
    )
    identity = PrivacyRequestIdentity(**{"email": salesforce_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = salesforce_connection_config.get_saas_config().fides_key
    merged_graph = salesforce_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [salesforce_connection_config],
        {"email": salesforce_identity_email},
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

    assert_rows_match(
        v[f"{dataset_name}:accounts"],
        min_size=1,
        keys=[
            "attributes",
            "Id",
            "IsDeleted",
            "MasterRecordId",
            "Name",
            "Type",
            "ParentId",
            "BillingStreet",
            "BillingCity",
            "BillingState",
            "BillingPostalCode",
            "BillingCountry",
            "BillingLatitude",
            "BillingLongitude",
            "BillingGeocodeAccuracy",
            "BillingAddress",
            "ShippingStreet",
            "ShippingCity",
            "ShippingState",
            "ShippingPostalCode",
            "ShippingCountry",
            "ShippingLatitude",
            "ShippingLongitude",
            "ShippingGeocodeAccuracy",
            "ShippingAddress",
            "Phone",
            "Fax",
            "AccountNumber",
            "Website",
            "PhotoUrl",
            "Sic",
            "Industry",
            "AnnualRevenue",
            "NumberOfEmployees",
            "Ownership",
            "TickerSymbol",
            "Description",
            "Rating",
            "Site",
            "OwnerId",
            "CreatedDate",
            "CreatedById",
            "LastModifiedDate",
            "LastModifiedById",
            "SystemModstamp",
            "LastActivityDate",
            "LastViewedDate",
            "LastReferencedDate",
            "Jigsaw",
            "JigsawCompanyId",
            "CleanStatus",
            "AccountSource",
            "DunsNumber",
            "Tradestyle",
            "NaicsCode",
            "NaicsDesc",
            "YearStarted",
            "SicDesc",
            "DandbCompanyId",
            "OperatingHoursId",
        ],
    )

    # verify we only returned data for our identity
    assert v[f"{dataset_name}:contacts"][0]["Email"] == salesforce_identity_email
    account_id = v[f"{dataset_name}:contacts"][0]["AccountId"]

    for case in v[f"{dataset_name}:cases"]:
        assert case["ContactEmail"] == salesforce_identity_email

    for lead in v[f"{dataset_name}:leads"]:
        assert lead["Email"] == salesforce_identity_email

    for campaign_member in v[f"{dataset_name}:campaign_members"]:
        assert campaign_member["Email"] == salesforce_identity_email

    for account in v[f"{dataset_name}:accounts"]:
        assert account["Id"] == account_id
