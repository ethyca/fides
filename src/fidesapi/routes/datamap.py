"""
Contains an endpoint for extracting a data map from the server
"""
from typing import Dict

from fastapi import APIRouter, Response, status
from fideslang.parse import parse_dict
from loguru import logger as log
from pandas import DataFrame

from fidesapi.routes.crud import get_resource, list_resource
from fidesapi.routes.util import API_PREFIX
from fidesapi.sql_models import sql_model_map
from fidesapi.utils.errors import DatabaseUnavailableError, NotFoundError
from fidesctl.core.export import build_joined_dataframe
from fidesctl.core.export_helpers import DATAMAP_COLUMNS

router = APIRouter(tags=["Datamap"], prefix=f"{API_PREFIX}/datamap")


@router.get(
    "/{organization_fides_key}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "content": {
                "application/json": {
                    "example": {"detail": "Unable to compile data map."}
                }
            }
        }
    },
)
async def export_datamap(organization_fides_key: str, response: Response) -> Dict:
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
            log.bind(error=error.detail["error"]).error("Resource not found")
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
