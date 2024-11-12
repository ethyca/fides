
from typing import Any, Dict, List

from loguru import logger

from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams

from fides.api.service.connectors.saas.authenticated_client import (
    AuthenticatedClient,
)

from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)

graphqlEndpoint = "/admin/api/2024-10/graphql.json"

@register("shopify_test_connection", [SaaSRequestType.TEST])
def shopify_test_connection(
    client: AuthenticatedClient,
    secrets: Dict[str, Any],
) -> int:

    payload = "{\"query\":\"{\\n  customers(first: 1) {\\n    edges {\\n      node {\\n        id\\n      }\\n    }\\n  }\\n}\",\"variables\":{}}"

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
    secrets: Dict[str, Any],
    input_data: Dict[str, List[Any]],

) -> int:

    output = []
    emails = input_data.get("email", [])

    for email in emails:

        payload = "{\"query\":\"query FindCustomersByEmail($emailQuery: String){\\n    customers(first: 10, query:$emailQuery) {\\n    edges {\\n      node {\\n        email\\n        id\\n        firstName\\n        lastName\\n        phone\\n        defaultAddress{\\n            name\\n            firstName\\n            lastName\\n            address1\\n            address2\\n            city\\n            province\\n            country\\n            zip\\n            phone\\n            provinceCode\\n            countryCodeV2\\n        }\\n        \\n      }\\n    }\\n            pageInfo {\\n            hasPreviousPage\\n            hasNextPage\\n            startCursor\\n            endCursor\\n        }\\n  }\\n}\",\"variables\":{\"emailQuery\":\"email:"+email+"\"}}"

        response = client.send(
            SaaSRequestParams(
                method=HTTPMethod.POST,
                body=payload,
                path=graphqlEndpoint,
            )
        )
        ## TODO: Add pagination support
        logger.info(response)
        ##TODO: check for correct data to append
        output.append(response)
    return output
