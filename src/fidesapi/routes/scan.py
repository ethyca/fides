"""
Contains all of the endpoints required to manage a scan of your resources.
"""
from enum import Enum
from typing import Dict

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from fidesapi.routes.crud import get_resource
from fidesapi.routes.util import API_PREFIX, unobscure
from fidesapi.sql_models import sql_model_map
from fidesctl.core.system import filter_aws_systems, generate_aws_systems


class ScanTypeEnum(str, Enum):
    """
    Scan Type Enum to capture the discrete possible values
    for a valid scan type
    """

    SYSTEM = "system"
    DATASET = "dataset"


class Scan(BaseModel):
    """
    The model for the request body housing scan information.
    """

    organization_key: str
    scan_type: ScanTypeEnum
    scan_target: str
    scan_config: Dict[str, str]


router = APIRouter(tags=["scan"], prefix=f"{API_PREFIX}/scan")

routers = [router]


@router.get("/", status_code=status.HTTP_200_OK)
async def validate_endpoint() -> Dict:
    """
    A canary endpoint to use when things don't seem quite right.
    """
    return {
        "status": "healthy",
        "version": "1.7.0",
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def generate_scan(scan_resource: Scan, response: Response) -> Dict:
    """
    Kicks off a generate command for fidesctl.

    Starting off, this will only take 'generate system aws'

    Debate is still up for if one endpoint makes sense or many, might be more
    difficult to document etc. with all of the config options.

    Currently follows the same logic as `generate_system_aws` in `system.py`
    """
    response.status_code = status.HTTP_201_CREATED
    aws_config = {
        "region_name": scan_resource.scan_config["region_name"],
        "aws_access_key_id": unobscure(
            scan_resource.scan_config["aws_access_key_id"]
        ).decode(),
        "aws_secret_access_key": unobscure(
            scan_resource.scan_config["aws_secret_access_key"]
        ).decode(),
    }

    organization_key = scan_resource.organization_key

    aws_systems = generate_aws_systems(
        organization_key=organization_key, aws_config=aws_config
    )

    organization = await get_resource(sql_model_map["organization"], organization_key)

    filtered_aws_systems = filter_aws_systems(
        systems=aws_systems, organization=organization
    )

    output_list_of_dicts = [i.dict(exclude_none=True) for i in filtered_aws_systems]
    return {"systems": output_list_of_dicts}
