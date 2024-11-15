from typing import Any, Dict, List

from loguru import logger
from requests import Response

from fides.api.graph.traversal import TraversalNode
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
from fides.api.util.collection_util import Row

graphqlEndpoint = "/admin/api/2024-10/graphql.json"


@register("shopify_test_connection", [SaaSRequestType.TEST])
def shopify_test_connection(
    client: AuthenticatedClient,
    secrets: Dict[str, Any],
) -> None:

    payload = '{"query":"{\\n  customers(first: 1) {\\n    edges {\\n      node {\\n        id\\n      }\\n    }\\n  }\\n}","variables":{}}'

    client.send(
        SaaSRequestParams(
            method=HTTPMethod.POST,
            body=payload,
            path=graphqlEndpoint,
        )
    )


@register("shopify_get_customers", [SaaSRequestType.READ])
def shopify_get_customers(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    output = []

    emails = input_data.get("email", [])
    for email in emails:

        output.extend(shopify_get_paginated_customer(client, email))

    return output


def shopify_get_paginated_customer(
    client: AuthenticatedClient, email: str, cursor: str = ""
) -> list[Row]:
    """
    Manages paginated requests for customers
    Cursor can be null for the first page
    """
    output = []
    basePayload = '{"query":"query FindCustomersByEmail($emailQuery: String, $customerEndCursor:String){\\n    customers(first: 10, after:$customerEndCursor, query:$emailQuery) {\\n    edges {\\n      node {\\n        email\\n        id\\n        firstName\\n        lastName\\n        phone\\n        defaultAddress{\\n            name\\n            firstName\\n            lastName\\n            address1\\n            address2\\n            city\\n            province\\n            country\\n            zip\\n            phone\\n            provinceCode\\n            countryCodeV2\\n        }\\n        \\n      }\\n    }\\n            pageInfo {\\n            hasPreviousPage\\n            hasNextPage\\n            startCursor\\n            endCursor\\n        }\\n  }\\n}",'
    if cursor:
        payload = (
            basePayload
            + '"variables":{"emailQuery":"email:'
            + email
            + '","customerEndCursor":"'
            + cursor
            + '"}}'
        )
    else:
        payload = basePayload + '"variables":{"emailQuery":"email:' + email + '"}}'

    response = client.send(
        SaaSRequestParams(
            method=HTTPMethod.POST,
            body=payload,
            path=graphqlEndpoint,
        )
    )

    ##TODO: check for correct data to append. Pop up the nest. Update the dataset
    nodes = response.json()["data"]["customers"]["edges"]
    for node in nodes:
        output.append(node["node"])

    page_data = response.json()["data"]["customers"]["pageInfo"]
    if page_data["hasNextPage"]:
        cursor = page_data["endCursor"]
        paginate_output = shopify_get_paginated_customer(client, email, cursor)
        output.extend(paginate_output)

    return output


@register("shopify_get_customer_orders", [SaaSRequestType.READ])
def shopify_get_customer_orders(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    output = []

    customer_ids = input_data.get("customer_id", [])

    for customer_id in customer_ids:
        ## For this query we have to strip down the global id to only the id numbers
        extracted_id = "".join(filter(str.isdigit, customer_id))
        output.extend(shopify_get_paginated_customer_orders(client, extracted_id))

    return output


def shopify_get_paginated_customer_orders(
    client: AuthenticatedClient, extracted_id: str, cursor: str = ""
) -> list[Row]:
    """
    Manages paginated requests for customer orders.
    Cursor can be null for the first page
    """
    output = []
    basePayload = '{"query":"query FindCustomersOrders($customerQuery: String, $orderEndCursor:String){\\n    orders(first: 10, after:$orderEndCursor query:$customerQuery) {\\n        edges {\\n            node {\\n                id\\n                billingAddress {\\n                    firstName\\n                    lastName\\n                    address1\\n                    address2\\n                    city\\n                    province\\n                    country\\n                    zip\\n                    phone\\n                }\\n                shippingAddress{\\n                    firstName\\n                    lastName\\n                    address1\\n                    address2\\n                    city\\n                    province\\n                    country\\n                    zip\\n                    phone\\n                }\\n                displayAddress{\\n                    firstName\\n                    lastName\\n                    address1\\n                    address2\\n                    city\\n                    province\\n                    country\\n                    zip\\n                    phone\\n                }\\n                email\\n                phone\\n                customerLocale\\n            }\\n        }\\n        pageInfo {\\n            hasPreviousPage\\n            hasNextPage\\n            startCursor\\n            endCursor\\n        }\\n    }\\n}",'

    if cursor:
        payload = (
            basePayload
            + '"variables":{"customerQuery":"customer_id:'
            + str(extracted_id)
            + '","orderEndCursor":"'
            + cursor
            + '"}}'
        )
    else:
        payload = (
            basePayload
            + '"variables":{"customerQuery":"customer_id:'
            + str(extracted_id)
            + '"}}'
        )

    response = client.send(
        SaaSRequestParams(
            method=HTTPMethod.POST,
            body=payload,
            path=graphqlEndpoint,
        )
    )

    nodes = response.json()["data"]["orders"]["edges"]
    for node in nodes:
        output.append(node["node"])

    page_data = response.json()["data"]["orders"]["pageInfo"]
    if page_data["hasNextPage"]:
        cursor = page_data["endCursor"]
        paginate_output = shopify_get_paginated_customer_orders(
            client, extracted_id, cursor
        )
        output.extend(paginate_output)

    return output


@register("shopify_get_customer_addresses", [SaaSRequestType.READ])
def shopify_get_customer_addresses(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:

    output = []
    customer_ids = input_data.get("customer_id", [])

    for customer_id in customer_ids:

        payload = (
            '{"query":"query($customerID: ID!){\\n    customer(id: $customerID){\\n        id,\\n        addresses {\\n            address1\\n            address2\\n            city\\n            province\\n            provinceCode\\n            country\\n            countryCodeV2\\n            zip\\n            formatted\\n        }\\n\\n    }\\n}",'
            + '"variables":{"customerID":"'
            + str(customer_id)
            + '"}}'
        )

        response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                body=payload,
                path=graphqlEndpoint,
            )
        )

        addresses = response.json()["data"]["customer"]["addresses"]
        for address in addresses:
            output.append(address)
            ##TODO: check for correct info on display. Might have to update Dataset
    return output


@register("shopify_get_blog_article_comments", [SaaSRequestType.READ])
def shopify_get_blog_article_comments(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:

    emails = input_data.get("email", [])

    output = shopify_get_paginated_blog_article_comments(client, emails)

    return output


def shopify_get_paginated_blog_article_comments(
    client: AuthenticatedClient, emails: List[str], cursor: str = ""
) -> list[Row]:
    output = []

    payload = '{"query":"query CommentList($endCursor:String){\\n    comments(first:100, after:$endCursor){\\n        nodes{\\n            id\\n            author{\\n                name\\n                email \\n            }\\n            body\\n        }\\n        pageInfo {\\n            hasPreviousPage\\n            hasNextPage\\n            startCursor\\n            endCursor\\n        }\\n    }\\n    \\n}","variables":{}}'

    if cursor:
        payload = payload + '"variables":{"orderEndCursor":"' + cursor + '"}}'

    response = client.send(
        SaaSRequestParams(
            method=HTTPMethod.POST,
            body=payload,
            path=graphqlEndpoint,
        )
    )

    nodes = response.json()["data"]["comments"]["nodes"]
    ##Filtering comments by author email
    for node in nodes:
        if node["author"]["email"] in emails:
            output.append(node)

    page_data = response.json()["data"]["comments"]["pageInfo"]
    if page_data["hasNextPage"]:
        cursor = page_data["endCursor"]
        paginate_output = shopify_get_paginated_blog_article_comments(
            client, emails, cursor
        )
        output.extend(paginate_output)

    return output


@register("shopify_delete_blog_article_comment", [SaaSRequestType.DELETE])
def shopify_delete_blog_article_comment(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:

    rows_deleted = 0

    for row_param_values in param_values_per_row:
        comment_id = row_param_values["comment_id"]

        payload = (
            '{"query":"mutation($commentID: ID!){\\n    commentDelete(id: $commentID){\\n    deletedCommentId\\n    userErrors {\\n      code\\n      field\\n      message\\n    }\\n  }\\n}\",'
            + '"variables":{"commentID":"'
            + str(comment_id)
            + '"}}'
        )
        response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                body=payload,
                path=graphqlEndpoint,
            )
        )

        handleErasureRequestErrors(response, "commentDelete")

        rows_deleted += 1

    return rows_deleted


@register("shopify_remove_customer_data", [SaaSRequestType.DELETE])
def shopify_remove_customer_data(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:

    rows_deleted = 0

    for row_param_values in param_values_per_row:
        customer_id = row_param_values["customer_id"]
        payload = (
            '{"query":"mutation customerRequestDataErasure($customerId: ID!) {\\n  customerRequestDataErasure(customerId: $customerId) {\\n    customerId\\n    userErrors {\\n      field\\n      message\\n    }\\n  }\\n}", '
            + '"variables":{"customerId":"'
            + str(customer_id)
            + '"}}'
        )

        response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                body=payload,
                path=graphqlEndpoint,
            )
        )

        handleErasureRequestErrors(response, "customerRequestDataErasure")

        rows_deleted += 1

    return rows_deleted


def handleErasureRequestErrors(response: Response, entityFieldName: str) -> None:
    """
    Manages common errors on Erasure Requests for this API
    """
    if "errors" in response.json():
        ##Notice: This can give error even when result status is 200
        logger.error(
            "Connector request failed with error message {}.", response.json()["errors"]
        )
        raise RequestFailureResponseException(response=response)

    entityRequestDataErasure = response.json()["data"][entityFieldName]
    if entityRequestDataErasure["userErrors"]:
        logger.error(
            "Connector request failed with error message {}.",
            entityRequestDataErasure["userErrors"],
        )
        raise RequestFailureResponseException(response=response)
