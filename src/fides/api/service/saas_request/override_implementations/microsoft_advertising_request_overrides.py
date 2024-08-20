from typing import Any, Dict, List
from defusedxml import ElementTree
from loguru import logger

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.logger_context_utils import request_details


sandbox_customer_manager_service_url = "https://clientcenter.api.sandbox.bingads.microsoft.com/Api/CustomerManagement/v13/CustomerManagementService.svc"
sandbox_campaing_manager_service_url = "https://campaign.api.sandbox.bingads.microsoft.com/Api/Advertiser/CampaignManagement/v13/CampaignManagementService.svc"
sandbox_bulk_api_url = "https://bulk.api.sandbox.bingads.microsoft.com/Api/Advertiser/CampaignManagement/v13/BulkService.svc?wsdl"


@register("microsoft_advertising_test_connection", [SaaSRequestType.TEST])
def microsoft_advertising_test_connection(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
    is_sandbox: bool = False
) -> int:
    rows_updated = 0

    access_token = secrets["access_token"]
    dev_token = secrets["dev_token"]

    for row_param_values in param_values_per_row:
        # API calls go here, look at other request overrides in this directory as examples


        rows_updated += 1

    return rows_updated



@register("microsoft_advertising_user_delete", [SaaSRequestType.DELETE])
def microsoft_advertising_user_delete(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
    is_sandbox: bool = False
) -> int:
    rows_updated = 0

    access_token = secrets["access_token"]
    dev_token = secrets["dev_token"]

    for row_param_values in param_values_per_row:
        # API calls go here, look at other request overrides in this directory as examples
        user_id = callGetUserRequestAndRetrieveUserId(client, dev_token, access_token)


        ## llamada 2

        ## Llamada 3

        ## Llamada 4

        ## Build Up del csv

        ##  Llamada 5. Enviar el CSv


        cliet.send(SaasRequestParams())
        rows_updated += 1

    return rows_updated

def getUserIdFromResponse(xmlRoot):
    """
    Retrieves the ID from the expected XML response of the GetUserRequest
    """
    ## TODO: Check if we can avoid this Nesting mess
    for branch in xmlRoot:
        if(branch.tag == "{http://schemas.xmlsoap.org/soap/envelope/}Body"):
            for leaf in branch:
                if(leaf.tag == "{https://bingads.microsoft.com/Customer/v13}GetUserResponse"):
                    for subleaf in leaf:
                        if(subleaf.tag== "{https://bingads.microsoft.com/Customer/v13}User"):
                            for user_leaf in subleaf:
                                if(user_leaf.tag == "{https://bingads.microsoft.com/Customer/v13/Entities}Id"):
                                    return user_leaf.text


def callGetUserRequestAndRetrieveUserId(client: AuthenticatedClient , developer_token: str, authentication_token: str):
    """
    Calls the GetUserRequest SOAP endpoint and retrieves the User ID from the response
    """

    payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:v13=\"https://bingads.microsoft.com/Customer/v13\">\n   <soapenv:Header>\n      <v13:DeveloperToken>" + developer_token + "</v13:DeveloperToken>\n      <v13:AuthenticationToken>" + authentication_token + "</v13:AuthenticationToken>\n   </soapenv:Header>\n   <soapenv:Body>\n      <v13:GetUserRequest>\n         <v13:UserId xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:nil=\"true\"/>\n      </v13:GetUserRequest>\n   </soapenv:Body>\n</soapenv:Envelope>"

    client.client_config.host = sandbox_customer_manager_service_url

    headers = {
        'Content-Type': 'text/xml',
        'SOAPAction': 'GetUser'
    }

    request_params = SaaSRequestParams(
        method=HTTPMethod.POST,
        path="",
        headers=headers,
        body=payload
    )
    response = client.send(
        request_params
    )

    context_logger = logger.bind(
        **request_details(
            client.get_authenticated_request(request_params), response
        )
    )

    user_id = getUserIdFromResponse(ElementTree.fromstring(response.text))

    if user_id is None:
        context_logger.error(
            "GetUser request failed with the following message {}.", response.text
        )

    return user_id
