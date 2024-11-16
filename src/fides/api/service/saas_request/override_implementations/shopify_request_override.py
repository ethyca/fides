import json
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
    payload = {
        "query": """
            query {
                customers(first: 1) {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
        """,
        "variables": {},
    }

    client.send(
        SaaSRequestParams(
            method=HTTPMethod.POST,
            body=json.dumps(payload),
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

    query = """
        query FindCustomersByEmail($emailQuery: String, $customerEndCursor: String) {
            customers(first: 10, after: $customerEndCursor, query: $emailQuery) {
                edges {
                    node {
                        email
                        id
                        firstName
                        lastName
                        phone
                        defaultAddress {
                            name
                            firstName
                            lastName
                            address1
                            address2
                            city
                            province
                            country
                            zip
                            phone
                            provinceCode
                            countryCodeV2
                        }
                    }
                }
                pageInfo {
                    hasPreviousPage
                    hasNextPage
                    startCursor
                    endCursor
                }
            }
        }
    """

    variables = {
        "emailQuery": f"email:{email}",
        "customerEndCursor": cursor if cursor else None,
    }

    payload = {"query": query, "variables": variables}

    response = client.send(
        SaaSRequestParams(
            method=HTTPMethod.POST,
            body=json.dumps(payload),
            path=graphqlEndpoint,
        )
    )

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

    query = """
        query FindCustomersOrders($customerQuery: String, $orderEndCursor: String) {
            orders(first: 10, after: $orderEndCursor, query: $customerQuery) {
                edges {
                    node {
                        id
                        billingAddress {
                            name
                            firstName
                            lastName
                            address1
                            address2
                            city
                            province
                            provinceCode
                            country
                            countryCodeV2
                            zip
                            phone
                        }
                        shippingAddress {
                            name
                            firstName
                            lastName
                            address1
                            address2
                            city
                            province
                            provinceCode
                            country
                            countryCodeV2
                            zip
                            phone
                        }
                        displayAddress {
                            name
                            firstName
                            lastName
                            address1
                            address2
                            city
                            province
                            provinceCode
                            country
                            countryCodeV2
                            zip
                            phone
                        }
                        email
                        phone
                        customerLocale
                    }
                }
                pageInfo {
                    hasPreviousPage
                    hasNextPage
                    startCursor
                    endCursor
                }
            }
        }
    """

    variables = {
        "customerQuery": f"customer_id:{extracted_id}",
        "orderEndCursor": cursor if cursor else None,
    }

    payload = {"query": query, "variables": variables}

    response = client.send(
        SaaSRequestParams(
            method=HTTPMethod.POST,
            body=json.dumps(payload),
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
        query = """
            query($customerID: ID!) {
                customer(id: $customerID) {
                    id
                    addresses {
                        id
                        name
                        firstName
                        lastName
                        phone
                        address1
                        address2
                        city
                        province
                        provinceCode
                        country
                        countryCodeV2
                        zip
                        formatted
                    }
                }
            }
        """

        payload = {"query": query, "variables": {"customerID": customer_id}}

        response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                body=json.dumps(payload),
                path=graphqlEndpoint,
            )
        )

        addresses = response.json()["data"]["customer"]["addresses"]
        for address in addresses:
            output.append(address)
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

    query = """
        query CommentList($endCursor: String) {
            comments(first: 100, after: $endCursor) {
                nodes {
                    id
                    author {
                        name
                        email
                    }
                    body
                }
                pageInfo {
                    hasPreviousPage
                    hasNextPage
                    startCursor
                    endCursor
                }
            }
        }
    """

    variables = {"endCursor": cursor if cursor else None}

    payload = {"query": query, "variables": variables}

    response = client.send(
        SaaSRequestParams(
            method=HTTPMethod.POST,
            body=json.dumps(payload),
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

        query = """
            mutation($commentID: ID!) {
                commentDelete(id: $commentID) {
                    deletedCommentId
                    userErrors {
                        code
                        field
                        message
                    }
                }
            }
        """

        payload = {"query": query, "variables": {"commentID": comment_id}}

        response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                body=json.dumps(payload),
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

        query = """
            mutation customerRequestDataErasure($customerId: ID!) {
                customerRequestDataErasure(customerId: $customerId) {
                    customerId
                    userErrors {
                        field
                        message
                    }
                }
            }
        """

        payload = {"query": query, "variables": {"customerId": customer_id}}

        response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                body=json.dumps(payload),
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
