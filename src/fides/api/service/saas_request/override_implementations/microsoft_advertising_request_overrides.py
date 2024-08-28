import csv
import hashlib
import json
import os
import shutil
from typing import Any, Dict, List, Optional
from xml.etree.ElementTree import Element

from defusedxml import ElementTree
from loguru import logger

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import (
    AuthenticatedClient,
    RequestFailureResponseException,
)
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.logger_context_utils import request_details

customer_manager_service_url = "https://clientcenter.api.bingads.microsoft.com/Api/CustomerManagement/v13/CustomerManagementService.svc"
campaing_manager_service_url = "https://campaign.api.bingads.microsoft.com/Api/Advertiser/CampaignManagement/v13/CampaignManagementService.svc"
bulk_api_url = "https://bulk.api.bingads.microsoft.com/Api/Advertiser/CampaignManagement/v13/BulkService.svc"

namespaces = {
    "soap": "http://schemas.xmlsoap.org/soap/envelope/",
    "ms_customer": "https://bingads.microsoft.com/Customer/v13",
    "ms_campaign": "https://bingads.microsoft.com/CampaignManagement/v13",
    "ent": "https://bingads.microsoft.com/Customer/v13/Entities",
}


@register("microsoft_advertising_test_connection", [SaaSRequestType.TEST])
def microsoft_advertising_test_connection(
    client: AuthenticatedClient,
    secrets: Dict[str, Any],
) -> int:
    """
    Tests the Microsoft Advertising Connection

    Attempts to retrieve the User ID  from the Microsoft Advertising API, checking that the tokens are valid tokens

    """
    rows_updated = 0

    access_token = secrets["access_token"]
    dev_token = secrets["dev_token"]

    callGetUserRequestAndRetrieveUserId(client, dev_token, access_token)

    return rows_updated + 1


@register("microsoft_advertising_user_delete", [SaaSRequestType.DELETE])
def microsoft_advertising_user_delete(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    """
    Process of removing an User email from the Microsoft Advertising Platform

    Gets the User ID, Account ID and Audiences List from the Microsoft Advertising API
    Builds up the CSV for removing the Customer List Object from the Audiences
    And finally gets the Bulk Upload URL to send the CSV
    """
    rows_updated = 0

    access_token = secrets["access_token"]
    dev_token = secrets["dev_token"]

    for row_param_values in param_values_per_row:

        user_id = callGetUserRequestAndRetrieveUserId(client, dev_token, access_token)

        account_ids = callGetAccountRequestAndRetrieveAccountsId(
            client, dev_token, access_token, user_id
        )

        for account_id in account_ids:

            audiences_list = callGetCustomerListAudiencesByAccounts(
                client, dev_token, access_token, user_id, account_id
            )

            if audiences_list is None:
                continue

            email = row_param_values["email"]
            csv_file = createCSVForRemovingCustomerListObject(audiences_list, email)

            upload_url = getBulkUploadURL(
                client, dev_token, access_token, user_id, account_id
            )

            bulkUploadCustomerList(
                client,
                upload_url,
                csv_file,
                dev_token,
                access_token,
                user_id,
                account_id,
            )

            os.remove(csv_file)

            rows_updated += 1

    return rows_updated


def getUserIdFromResponse(xmlRoot: Element) -> Optional[str]:
    """
    Retrieves the ID from the expected XML response of the GetUserRequest
    """
    xpath = "./soap:Body/ms_customer:GetUserResponse/ms_customer:User/ent:Id"
    id_element = xmlRoot.find(xpath, namespaces)

    if id_element is not None:
        return id_element.text

    return None


def callGetUserRequestAndRetrieveUserId(
    client: AuthenticatedClient, developer_token: str, authentication_token: str
) -> str:
    """
    Calls the GetUserRequest SOAP endpoint and retrieves the User ID from the response
    """

    payload = (
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v13="https://bingads.microsoft.com/Customer/v13">\n   <soapenv:Header>\n      <v13:DeveloperToken>'
        + developer_token
        + "</v13:DeveloperToken>\n      <v13:AuthenticationToken>"
        + authentication_token
        + '</v13:AuthenticationToken>\n   </soapenv:Header>\n   <soapenv:Body>\n      <v13:GetUserRequest>\n         <v13:UserId xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>\n      </v13:GetUserRequest>\n   </soapenv:Body>\n</soapenv:Envelope>'
    )

    client.uri = customer_manager_service_url

    headers = {"Content-Type": "text/xml", "SOAPAction": "GetUser"}

    request_params = SaaSRequestParams(
        method=HTTPMethod.POST, path="", headers=headers, body=payload
    )
    response = client.send(request_params)

    context_logger = logger.bind(
        **request_details(client.get_authenticated_request(request_params), response)
    )

    user_id = getUserIdFromResponse(ElementTree.fromstring(response.text))

    if user_id is None:
        context_logger.error(
            "GetUser request failed with the following message {}.", response.text
        )

        raise RequestFailureResponseException(response=response)

    return user_id


def getAccountsIdFromResponse(xmlRoot: Element) -> Optional[List[str]]:
    """
    Retrieves the ID from the expected XML response of the SearchAccountsRequest
    TODO: Expand for Multiple accounts
    """
    # Use XPath to directly find the Id element
    accounts_id: List[str] = []
    xpath = "./soap:Body/ms_customer:SearchAccountsResponse/ms_customer:Accounts"
    accounts_element = xmlRoot.find(xpath, namespaces)

    if accounts_element is None:
        return None

    xmlSubpath = "./ent:Id"
    for account_element in accounts_element:
        account_id = account_element.find(xmlSubpath, namespaces)
        if account_id is not None:
            appendTextFromElementToList(account_id, accounts_id)

    return accounts_id


def callGetAccountRequestAndRetrieveAccountsId(
    client: AuthenticatedClient,
    developer_token: str,
    authentication_token: str,
    user_id: str,
) -> List[str]:
    """
    Calls the SearchAccounts SOAP endpoint and retrieves the Account ID from the response
    """

    payload = (
        '<?xml version="1.0" encoding="utf-8"?>\n<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">\n  <s:Header>\n    <h:ApplicationToken i:nil="true" xmlns:h="https://bingads.microsoft.com/Customer/v13" xmlns:i="http://www.w3.org/2001/XMLSchema-instance" />\n    <h:AuthenticationToken xmlns:h="https://bingads.microsoft.com/Customer/v13">'
        + authentication_token
        + '</h:AuthenticationToken>\n    <h:DeveloperToken xmlns:h="https://bingads.microsoft.com/Customer/v13">'
        + developer_token
        + '</h:DeveloperToken>\n  </s:Header>\n  <s:Body>\n    <SearchAccountsRequest xmlns="https://bingads.microsoft.com/Customer/v13">\n      <Predicates xmlns:a="https://bingads.microsoft.com/Customer/v13/Entities" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">\n        <a:Predicate>\n          <a:Field>UserId</a:Field>\n          <a:Operator>Equals</a:Operator>\n          <a:Value>'
        + user_id
        + '</a:Value>\n        </a:Predicate>\n      </Predicates>\n      <Ordering i:nil="true" xmlns:a="https://bingads.microsoft.com/Customer/v13/Entities" xmlns:i="http://www.w3.org/2001/XMLSchema-instance" />\n      <PageInfo xmlns:a="https://bingads.microsoft.com/Customer/v13/Entities" xmlns:i="http://www.w3.org/2001/XMLSchema-instance">\n        <a:Index>0</a:Index>\n        <a:Size>10</a:Size>\n      </PageInfo>\n    </SearchAccountsRequest>\n  </s:Body>\n</s:Envelope>\n'
    )

    headers = {"Content-Type": "text/xml", "SOAPAction": "SearchAccounts"}

    client.uri = customer_manager_service_url

    request_params = SaaSRequestParams(
        method=HTTPMethod.POST, path="", headers=headers, body=payload
    )

    response = client.send(request_params)

    context_logger = logger.bind(
        **request_details(client.get_authenticated_request(request_params), response)
    )

    accountIds = getAccountsIdFromResponse(ElementTree.fromstring(response.text))

    if accountIds is None:
        context_logger.error(
            "SearchAccounts request failed with the following message {}.",
            response.text,
        )

        raise RequestFailureResponseException(response=response)

    context_logger.info(
        "SearchAccounts request was succesfull with the following ids {}.", accountIds
    )

    return accountIds


def getAudiencesIDsfromResponse(xmlRoot: Element) -> Optional[List[str]]:
    """
    Gets the Audience _ids from the GetAudiencesByIdsResponse
    """

    audience_ids: List[str] = []
    xpath = "./soap:Body/ms_campaign:GetAudiencesByIdsResponse/ms_campaign:Audiences"
    audiences_element = xmlRoot.find(xpath, namespaces)

    if audiences_element is None:
        return None

    for audience_leaf in audiences_element:
        xmlSubpath = "./ms_campaign:Id"
        audience_id = audience_leaf.find(xmlSubpath, namespaces)
        if audience_id is not None:
            appendTextFromElementToList(audience_id, audience_ids)

    return audience_ids


def callGetCustomerListAudiencesByAccounts(
    client: AuthenticatedClient,
    developer_token: str,
    authentication_token: str,
    user_id: str,
    account_id: str,
) -> Optional[list[str]]:
    payload = (
        '<s:Envelope xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">\n  <s:Header xmlns="https://bingads.microsoft.com/CampaignManagement/v13">\n    <Action mustUnderstand="1">GetAudiencesByIds</Action>\n   <AuthenticationToken i:nil="false">'
        + authentication_token
        + '</AuthenticationToken>\n  <CustomerAccountId i:nil="false">'
        + account_id
        + '</CustomerAccountId>\n    <CustomerId i:nil="false">'
        + user_id
        + '</CustomerId>\n    <DeveloperToken i:nil="false">'
        + developer_token
        + '</DeveloperToken>\n  </s:Header>\n  <s:Body>\n    <GetAudiencesByIdsRequest xmlns="https://bingads.microsoft.com/CampaignManagement/v13">\n      <Type>CustomerList</Type>\n    </GetAudiencesByIdsRequest>\n  </s:Body>\n</s:Envelope>\n'
    )

    headers = {
        "Content-Type": "text/xml",
        "SOAPAction": "GetAudiencesByIds",
    }

    client.uri = campaing_manager_service_url

    request_params = SaaSRequestParams(
        method=HTTPMethod.POST, path="", headers=headers, body=payload
    )

    response = client.send(request_params)

    context_logger = logger.bind(
        **request_details(client.get_authenticated_request(request_params), response)
    )

    audiences_list = getAudiencesIDsfromResponse(ElementTree.fromstring(response.text))

    if not audiences_list:
        ## Caveat: Do we want to throw error when the Audiences is empty?
        context_logger.error(
            "GetAudiencesByIds collected No audiences {}.", response.text
        )

        return None

    return audiences_list


def createCSVForRemovingCustomerListObject(
    audiences_ids: List[str], target_email: str
) -> str:
    """
    Createsa CSV with the values to remove the Customer List Objects.
    Since we dont know on Which Audience the Customer List Object is, we will remove it from all the Audiences
    """

    base_filepath = "src/fides/api/service/saas_request/upload_files_templates/CustomerListRemoval.csv"
    destination = "CustomerListRemoval.csv"
    csv_headers = [
        "Type",
        "Status",
        "Id",
        "Parent Id",
        "Client Id",
        "Modified Time",
        "Name",
        "Description",
        "Scope",
        "Audience",
        "Action Type",
        "SubType",
        "Text",
    ]

    hashedEmail = hashlib.sha256(target_email.encode()).hexdigest()

    shutil.copyfile(base_filepath, destination)

    with open(destination, "a", encoding="utf8") as csvfile:
        writer = csv.DictWriter(csvfile, csv_headers)
        for audience_id in audiences_ids:
            writer.writerow(
                {
                    "Type": "Customer List",
                    "Id": audience_id,
                    "Client Id": "fides_ethyca",
                    "Action Type": "Update",
                }
            )
            writer.writerow(
                {
                    "Type": "Customer List Item",
                    "Parent Id": audience_id,
                    "Action Type": "Delete",
                    "SubType": "Email",
                    "Text": hashedEmail,
                }
            )

    return destination


def getUploadURLFromResponse(xmlRoot: Element) -> Optional[str]:

    xpath = "./soap:Body/ms_campaign:GetBulkUploadUrlResponse/ms_campaign:UploadUrl"
    upload_url_element = xmlRoot.find(xpath, namespaces)

    if upload_url_element is not None:
        return upload_url_element.text
    return None


def getBulkUploadURL(
    client: AuthenticatedClient,
    developer_token: str,
    authentication_token: str,
    user_id: str,
    account_id: str,
) -> str:

    payload = (
        '<s:Envelope xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">\n  <s:Header xmlns="https://bingads.microsoft.com/CampaignManagement/v13">\n    <Action mustUnderstand="1">GetBulkUploadUrl</Action>\n   <AuthenticationToken i:nil="false">'
        + authentication_token
        + '</AuthenticationToken>\n    <CustomerAccountId i:nil="false">'
        + account_id
        + '</CustomerAccountId>\n    <CustomerId i:nil="false">'
        + user_id
        + '</CustomerId>\n    <DeveloperToken i:nil="false">'
        + developer_token
        + '</DeveloperToken>\n  </s:Header>\n  <s:Body>\n    <GetBulkUploadUrlRequest xmlns="https://bingads.microsoft.com/CampaignManagement/v13">\n      <ResponseMode>ErrorsAndResults</ResponseMode>\n      <AccountId>'
        + account_id
        + "</AccountId>\n    </GetBulkUploadUrlRequest>\n  </s:Body>\n</s:Envelope>\n"
    )
    headers = {
        "Content-Type": "text/xml",
        "SOAPAction": "GetBulkUploadUrl",
    }

    client.uri = bulk_api_url

    request_params = SaaSRequestParams(
        method=HTTPMethod.POST, path="", headers=headers, body=payload
    )

    response = client.send(request_params)

    context_logger = logger.bind(
        **request_details(client.get_authenticated_request(request_params), response)
    )

    upload_url = getUploadURLFromResponse(ElementTree.fromstring(response.text))

    if not upload_url:
        context_logger.error(
            "GetBulkUploadUrl collected No upload URL {}.", response.text
        )
        raise RequestFailureResponseException(response=response)

    return upload_url


### Step 6 : Upload to the API


def bulkUploadCustomerList(
    client: AuthenticatedClient,
    url: str,
    filepath: str,
    developer_token: str,
    authentication_token: str,
    user_id: str,
    account_id: str,
) -> bool:

    headers = {
        "AuthenticationToken": authentication_token,
        "DeveloperToken": developer_token,
        "CustomerId": user_id,
        "AccountId": account_id,
    }

    ## using with open for memory allocation. See https://pylint.pycqa.org/en/latest/user_guide/messages/refactor/consider-using-with.html
    with open(filepath, "rb") as file:

        upload_files = [
            (
                "uploadFile",
                (
                    "customerlist.csv",
                    file,
                    "application/octet-stream",
                ),
            )
        ]

        client.uri = url

        request_params = SaaSRequestParams(
            method=HTTPMethod.POST, headers=headers, path="", files=upload_files
        )

        response = client.send(
            request_params,
        )

        context_logger = logger.bind(
            **request_details(
                client.get_authenticated_request(request_params), response
            )
        )

        parsedResponse = json.loads(response.text)

        if not parsedResponse["TrackingId"]:
            context_logger.error(
                "GetBulkUploadUrl collected No upload URL {}.", response.text
            )
            raise RequestFailureResponseException(response=response)

        ## Do we need a process to check the status of the Upload?
        ## How are we persisting data?
        context_logger.info(
            "Tracking ID of the recent upload: {}.", parsedResponse["TrackingId"]
        )

    return True


def appendTextFromElementToList(element: Element, list_of_elements: List[str]) -> None:
    """
    Safely retrieves the text from the Element and appends it to the list
    """
    if element is not None:
        if element.text is not None:
            list_of_elements.append(element.text)
