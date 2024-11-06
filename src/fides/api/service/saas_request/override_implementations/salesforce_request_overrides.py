from json import dumps
from typing import Any, Dict, List

from loguru import logger

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)


def truncate_fields_to_40_characters(masked_object_fields: Dict) -> Dict:
    """
    Check if the masked field is over 40 characters long, if so truncate it to 40 characters.
    """
    for key in masked_object_fields:
        if (
            isinstance(masked_object_fields[key], str)
            and len(masked_object_fields[key]) > 40
        ):
            logger.info("Truncating {key} field to 40 characters")
            masked_object_fields[key] = masked_object_fields[key][:40]
    return masked_object_fields


def mask_email(masked_object_fields: Dict, email_field: str) -> Dict:
    """
    Masking Email properly so it does not breaks validation rules
    """
    if email_field in masked_object_fields:
        masked_object_fields[email_field] = "masked@company.com"
    return masked_object_fields


@register("salesforce_contacts_update", [SaaSRequestType.UPDATE])
def salesforce_contacts_update(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_updated = 0
    # each update_params dict correspond to a record that needs to be updated
    for row_param_values in param_values_per_row:

        masked_object_fields = row_param_values["masked_object_fields"]

        masked_object_fields = mask_email(masked_object_fields, "Email")

        masked_object_fields = truncate_fields_to_40_characters(masked_object_fields)

        update_body = dumps(masked_object_fields)
        contact_id = row_param_values["contact_id"]
        client.send(
            SaaSRequestParams(
                method=HTTPMethod.PATCH,
                headers={"Content-Type": "application/json"},
                path=f"/services/data/v54.0/sobjects/Contact/{contact_id}",
                body=update_body,
            )
        )
        rows_updated += 1
    return rows_updated


@register("salesforce_cases_update", [SaaSRequestType.UPDATE])
def salesforce_cases_update(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_updated = 0
    # each update_params dict correspond to a record that needs to be updated
    for row_param_values in param_values_per_row:
        masked_object_fields = row_param_values["masked_object_fields"]

        masked_object_fields = mask_email(masked_object_fields, "SuppliedEmail")

        masked_object_fields = truncate_fields_to_40_characters(masked_object_fields)

        update_body = dumps(masked_object_fields)
        case_id = row_param_values["case_id"]
        client.send(
            SaaSRequestParams(
                method=HTTPMethod.PATCH,
                headers={"Content-Type": "application/json"},
                path=f"/services/data/v54.0/sobjects/Case/{case_id}",
                body=update_body,
            )
        )
        rows_updated += 1
    return rows_updated


@register("salesforce_leads_update", [SaaSRequestType.UPDATE])
def salesforce_leads_update(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    rows_updated = 0
    # each update_params dict correspond to a record that needs to be updated
    for row_param_values in param_values_per_row:
        masked_object_fields = row_param_values["masked_object_fields"]

        masked_object_fields = mask_email(masked_object_fields, "Email")

        masked_object_fields = truncate_fields_to_40_characters(masked_object_fields)

        update_body = dumps(masked_object_fields)
        lead_id = row_param_values["lead_id"]
        client.send(
            SaaSRequestParams(
                method=HTTPMethod.PATCH,
                headers={"Content-Type": "application/json"},
                path=f"/services/data/v54.0/sobjects/Lead/{lead_id}",
                body=update_body,
            )
        )
        rows_updated += 1
    return rows_updated
