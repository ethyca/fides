"""
Contains all of the endpoints required to manage a scan of your resources.
"""
from enum import Enum
from typing import Dict, List, Union, cast

from fastapi import APIRouter, Response, status
from fideslang.models import Organization
from loguru import logger as log
from pydantic import BaseModel

from fidesapi.routes.crud import get_resource
from fidesapi.routes.util import API_PREFIX, unobscure_string
from fidesapi.sql_models import sql_model_map
from fidesapi.utils import errors
from fidesctl.core.system import generate_aws_systems


class ScanTypeEnum(str, Enum):
    """
    Scan Type Enum to capture the discrete possible values
    for a valid scan type
    """

    SYSTEM = "system"
    DATASET = "dataset"


class AWSConfig(BaseModel):
    """
    The model for the connection config for AWS
    """

    region_name: str
    aws_secret_access_key: str
    aws_access_key_id: str


class OktaConfig(BaseModel):
    """
    The model for the connection config for Okta
    """

    okta_client_token: str


class Scan(BaseModel):
    """
    The model for the request body housing scan information.
    """

    organization_key: str
    scan_type: ScanTypeEnum
    scan_target: str
    scan_config: Union[AWSConfig, OktaConfig]


router = APIRouter(tags=["scan"], prefix=f"{API_PREFIX}/scan")

routers = [router]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def generate_scan(scan_resource: Scan, response: Response) -> Dict:
    """
    Kicks off a generate command for fidesctl.

    Starting off, this will only take 'generate system aws'

    Debate is still up for if one endpoint makes sense or many, might be more
    difficult to document etc. with all of the config options.

    Currently follows the same logic as `generate_system_aws` in `system.py`
    """

    organization = await get_resource(
        sql_model_map["organization"], scan_resource.organization_key
    )
    if scan_resource.scan_target.lower() == "aws":
        log.info("Setting config for AWS")
        output_list_of_dicts = generate_aws(
            aws_config=cast(AWSConfig, scan_resource.scan_config),
            organization=organization,
        )

    response.status_code = (
        status.HTTP_200_OK
        if len(output_list_of_dicts) > 0
        else status.HTTP_204_NO_CONTENT
    )
    return {"systems": output_list_of_dicts}


def generate_aws(
    aws_config: AWSConfig, organization: Organization
) -> List[Dict[str, str]]:
    """
    Returns a list of Systems found in AWS.
    """
    config = {
        "region_name": aws_config.region_name,
        "aws_access_key_id": unobscure_string(aws_config.aws_access_key_id),
        "aws_secret_access_key": unobscure_string(aws_config.aws_secret_access_key),
    }
    try:
        log.info("Generating systems from AWS")
        aws_systems = generate_aws_systems(organization=organization, aws_config=config)
    except:
        error = errors.FailedConnectionError()
        log.bind(error=error.detail["error"]).error("Failed to scan AWS")
        raise error

    output_list_of_dicts = [i.dict(exclude_none=True) for i in aws_systems]
    return output_list_of_dicts


# def generate_okta() -> List[Dict[str, str]]:
#     return None


# def generate_okta() -> List[Dict[str, str]]:
#     return None
