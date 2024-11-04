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


# check if the masked field is over 40 characters long
# if so, truncate it to 40 characters
def truncateFieldsTo40Characters(masked_object_fields: Dict) -> Dict:
    for key in masked_object_fields:
        logger.info(key)
        logger.info((masked_object_fields[key]))
        if not isinstance(masked_object_fields[key], str):
            continue
        if len(masked_object_fields[key]) > 40:
            masked_object_fields[key] = masked_object_fields[key][:40]
    return masked_object_fields


# Masking Email properly so it does not breaks validation rules
# using the privacy request id to have an unique id
def maskEmail(masked_object_fields: Dict, email_field: str) -> Dict:
    if email_field in masked_object_fields:
        masked_object_fields[email_field] = "Masked@company.com"
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

        masked_object_fields = maskEmail(masked_object_fields, "Email")

        masked_object_fields = truncateFieldsTo40Characters(masked_object_fields)

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

        masked_object_fields = maskEmail(masked_object_fields, "SuppliedEmail")

        masked_object_fields = truncateFieldsTo40Characters(masked_object_fields)

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

        masked_object_fields = maskEmail(masked_object_fields, "Email")

        masked_object_fields = truncateFieldsTo40Characters(masked_object_fields)

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


@register("salesforce_campaign_members_update", [SaaSRequestType.UPDATE])
def salesforce_campaign_members_update(
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

        masked_object_fields = maskEmail(masked_object_fields, "Email")

        masked_object_fields = truncateFieldsTo40Characters(masked_object_fields)

        update_body = dumps(masked_object_fields)
        campaign_member_id = row_param_values["campaign_member_id"]
        client.send(
            SaaSRequestParams(
                method=HTTPMethod.PATCH,
                headers={"Content-Type": "application/json"},
                path=f"/services/data/v54.0/sobjects/CampaignMember/{campaign_member_id}",
                body=update_body,
            )
        )
        rows_updated += 1
    return rows_updated
