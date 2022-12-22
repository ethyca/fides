"""
Contains an endpoint for extracting a data map from the server
"""
from typing import Dict, List

from fastapi import Response, status
from fideslang.parse import parse_dict
from loguru import logger as log
from pandas import DataFrame

from fides.api.ctl.database.crud import get_resource, list_resource
from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.sql_models import sql_model_map  # type: ignore[attr-defined]
from fides.api.ctl.utils.api_router import APIRouter
from fides.api.ctl.utils.errors import DatabaseUnavailableError, NotFoundError
from fides.core.export import build_joined_dataframe
from fides.core.export_helpers import DATAMAP_COLUMNS

API_EXTRA_COLUMNS = {
    "system.fides_key": "System Fides Key",
    "dataset.fides_key": "Dataset Fides Key (if applicable)",
    "system.system_dependencies": "Related cross-system dependencies",
    "system.description": "Description of the System",
    "system.ingress": "Related Systems which receive data to this System",
    "system.egress": "Related Systems which send data to this System",
}
DATAMAP_COLUMNS_API = {**DATAMAP_COLUMNS, **API_EXTRA_COLUMNS}

router = APIRouter(tags=["Datamap"], prefix=f"{API_PREFIX}/datamap")


@router.get(
    "/{organization_fides_key}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": [
                        DATAMAP_COLUMNS_API,
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
                            "dataset.source_name": "N/A",
                            "third_country_combined": "GBR, USA, CAN",
                            "unioned_data_categories": "user.contact",
                            "dataset.retention": "N/A",
                            "system.joint_controller": "",
                            "system.third_country_safeguards": "",
                            "system.link_to_processor_contract": "",
                            "organization.link_to_security_policy": "https://ethyca.com/privacy-policy/",
                            "system.fides_key": "",
                            "dataset.fides_key": "",
                            "system.system_dependencies": "",
                            "system.description": "",
                            "system.ingress": [],
                            "system.egress": [],
                        },
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
) -> List[Dict[str, str]]:
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
            not_found_error = NotFoundError(
                "organization", organization_fides_key, "Resource not found."
            )
            log.bind(error=not_found_error.detail["error"]).error(  # type: ignore[index]
                "No organizations found"
            )
            raise not_found_error
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
        database_unavailable_error = DatabaseUnavailableError(
            error_message="Database unavailable"
        )
        log.bind(error=not_found_error.detail["error"]).error(  # type: ignore[index]
            "Database unavailable"
        )
        raise database_unavailable_error

    joined_system_dataset_df = build_joined_dataframe(server_resource_dict)

    formatted_datamap = format_datamap_values(joined_system_dataset_df)

    # prepend column names
    formatted_datamap = [DATAMAP_COLUMNS_API] + formatted_datamap
    return formatted_datamap


def format_datamap_values(joined_system_dataset_df: DataFrame) -> List[Dict[str, str]]:
    """
    Formats the joined DataFrame to return the data as records.
    """

    limited_columns_df = DataFrame(
        joined_system_dataset_df,
        columns=list(DATAMAP_COLUMNS_API.keys()),
    )

    return limited_columns_df.to_dict("records")
