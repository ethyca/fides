"""
Contains an endpoint for extracting a data map from the server
"""
from typing import Dict

from fastapi import Response, status
from fideslang.parse import parse_dict
from loguru import logger as log
from pandas import DataFrame

from fidesapi.routes.crud import get_resource, list_resource
from fidesapi.routes.util import API_PREFIX
from fidesapi.sql_models import sql_model_map
from fidesapi.utils.api_router import APIRouter
from fidesapi.utils.errors import DatabaseUnavailableError, NotFoundError
from fidesctl.core.export import build_joined_dataframe
from fidesctl.core.export_helpers import DATAMAP_COLUMNS

router = APIRouter(tags=["Datamap"], prefix=f"{API_PREFIX}/datamap")


@router.get(
    "/{organization_fides_key}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": [
                        {
                            "system.name": "Demo Analytics System",
                            "system.data_responsibility_title": "Controller",
                            "system.administrating_department": "Engineering",
                            "system.privacy_declaration.data_use.name": "System",
                            "system.privacy_declaration.data_use.legal_basis": "N/A",
                            "system.privacy_declaration.data_use.special_category": "N/A",
                            "system.privacy_declaration.data_use.recipients": "N/A",
                            "system.privacy_declaration.data_use.legitimate_interest": "N/A",
                            "system.privacy_declaration.data_use.legitimate_interest_impact_assessment": "N/A",
                            "system.privacy_declaration.data_subjects.name": "Customer",
                            "system.privacy_declaration.data_subjects.rights_available": "No data subject rights listed",
                            "system.privacy_declaration.data_subjects.automated_decisions_or_profiling": "N/A",
                            "system.data_protection_impact_assessment.is_required": "true",
                            "system.data_protection_impact_assessment.progress": "Complete",
                            "system.data_protection_impact_assessment.link": "https://example.org/analytics_system_data_protection_impact_assessment",
                            "dataset.name": "N/A",
                            "third_country_combined": "GBR, USA, CAN",
                            "unioned_data_categories": "user.provided.identifiable.contact",
                            "dataset.retention": "N/A",
                            "system.joint_controller": "",
                            "system.third_country_safeguards": "",
                            "system.link_to_processor_contract": "",
                            "organization.link_to_security_policy": "https://ethyca.com/privacy-policy/",
                        }
                    ]
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "content": {
                "application/json": {
                    "example": {"detail": "Unable to compile data map."}
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "content": {
                "application/json": {"example": {"detail": "Resource not found."}}
            }
        },
    },
)
async def export_datamap(
    organization_fides_key: str, response: Response
) -> Dict[str, str]:
    """
    An endpoint to return the data map for a given Organization.

    The Organization `fides_key` is the only url parameter required. In most cases,
    this should be `default_organization`

    Uses shared logic from the CLI, first gathering all resources from the server then
    formatting all attributes appropriately.

    Returns the expected datamap for a given organization fides key as a set of records.
    """
    # load resources from server, filtered by organization
    try:
        try:
            organization = await get_resource(
                sql_model_map["organization"], organization_fides_key
            )
        except NotFoundError:
            error = NotFoundError("organization", organization_fides_key)
            log.bind(error=error.detail["error"]).error("Resource not found.")
            raise error
        server_resource_dict = {"organization": [organization]}

        for resource_type in ["system", "dataset", "data_subject", "data_use"]:
            server_resources = await list_resource(sql_model_map[resource_type])
            filtered_server_resources = [
                parse_dict(resource_type, resource.__dict__, from_server=True)
                for resource in server_resources
                if resource.organization_fides_key == organization_fides_key
            ]
            server_resource_dict[resource_type] = filtered_server_resources
    except DatabaseUnavailableError:
        error = DatabaseUnavailableError()
        log.bind(error=error.detail["error"]).error("Database unavailable")
        raise error

    joined_system_dataset_df = build_joined_dataframe(server_resource_dict)

    formatted_datamap = format_datamap_values(joined_system_dataset_df)

    return formatted_datamap


def format_datamap_values(joined_system_dataset_df: DataFrame) -> Dict[str, str]:
    """
    Formats the joined DataFrame to return the data as records.
    """

    limited_columns_df = joined_system_dataset_df[
        joined_system_dataset_df.columns[
            joined_system_dataset_df.columns.isin(DATAMAP_COLUMNS)
        ]
    ]
    return limited_columns_df.to_dict("records")
