"""
Contains an endpoint for extracting a data map from the server
"""
from typing import Dict

from fastapi import APIRouter, Response, status

from fidesapi.routes.crud import get_resource, list_resource
from fidesapi.routes.util import API_PREFIX
from fidesapi.sql_models import sql_model_map

router = APIRouter(tags=["Datamap"], prefix=f"{API_PREFIX}/datamap")


@router.get("/", status_code=status.HTTP_200_OK)
async def validate_endpoint() -> Dict:
    """
    A canary endpoint to use when things don't seem quite right.
    """
    return {
        "status": "healthy",
        "version": "1.7.0",
    }


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
    Returns the expected datamap for a given organization fides key.
    """
    # load resources from server, filtered by organization
    organization = await get_resource(
        sql_model_map["organization"], organization_fides_key
    )
    server_resource_dict = {"organization": [organization]}
    for resource_type in ["system", "dataset"]:
        server_resources = await list_resource(sql_model_map[resource_type])

        filtered_server_resources = [
            resource
            for resource in server_resources
            if resource.organization_fides_key == organization_fides_key
        ]
        server_resource_dict[resource_type] = filtered_server_resources

    return server_resource_dict
