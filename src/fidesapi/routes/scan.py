"""
Contains all of the endpoints required to manage a scan of your resources.
"""
from enum import Enum
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Response, status
from fideslang.models import Organization, System
from loguru import logger as log
from pydantic import BaseModel

from fidesapi.routes.crud import get_resource
from fidesapi.routes.util import API_PREFIX, unobscure_string
from fidesapi.sql_models import sql_model_map
from fidesctl.core.system import generate_aws_systems


class ScanTypes(str, Enum):
    """
    Scan Type Enum to capture the discrete possible values
    for a valid scan type
    """

    SYSTEM = "systems"
    DATASET = "datasets"


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
    Defines attributes of the scan included in a request.
    """

    config: Union[AWSConfig, OktaConfig]
    target: str
    type: ScanTypes


class ScanRequestPayload(BaseModel):
    """
    The model for the request body housing scan information.
    """

    organization_key: str
    scan: Scan


class ScannedResponse(BaseModel):
    """
    The model to hous the response for scanned infrastructure.
    """

    scan_results: Optional[List[System]]


router = APIRouter(tags=["Scan"], prefix=f"{API_PREFIX}/scan")


@router.post(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=ScannedResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "content": {
                "application/json": {"example": {"detail": "Unable to perform scan."}}
            }
        },
    },
)
async def generate_scan(
    scan_request_payload: ScanRequestPayload, response: Response
) -> Dict:
    """
    Kicks off a generate command for fidesctl.

    Starting off, this will only generate systems from AWS

    Initial plan is to have one endpoint handle scanning different
    infrastructure (e.g. aws, okta) with separate config options.

    Currently follows the same logic as `generate_system_aws` in `system.py`

    Config secrets should be encoded as a minor security precaution.
    All production deployments should implement HTTPS
    """
    organization = await get_resource(
        sql_model_map["organization"], scan_request_payload.organization_key
    )
    if scan_request_payload.scan.target.lower() == "aws":
        try:
            import boto3  # pylint: disable=unused-import
        except ModuleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Packages not found, ensure aws is included: fidesctl[aws]",
            )
        log.info("Setting config for AWS")
        generated_systems = generate_aws(
            aws_config=AWSConfig(**scan_request_payload.scan.config.dict()),
            organization=organization,
        )
    return {"scan_results": generated_systems}


def generate_aws(
    aws_config: AWSConfig, organization: Organization
) -> List[Dict[str, str]]:
    """
    Returns a list of Systems found in AWS.
    """
    from botocore.exceptions import ClientError

    config = {
        "region_name": aws_config.region_name,
        "aws_access_key_id": unobscure_string(aws_config.aws_access_key_id),
        "aws_secret_access_key": unobscure_string(aws_config.aws_secret_access_key),
    }
    try:
        log.info("Generating systems from AWS")
        aws_systems = generate_aws_systems(organization=organization, aws_config=config)
    except ClientError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to complete scan"
        )

    return [i.dict(exclude_none=True) for i in aws_systems]
