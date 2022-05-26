"""
Contains all of the endpoints required to manage generating resources.
"""
from enum import Enum
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Response, status
from fideslang.models import Dataset, Organization, System
from loguru import logger as log
from pydantic import BaseModel, root_validator

from fidesapi.routes.crud import get_resource
from fidesapi.routes.util import API_PREFIX, unobscure_string
from fidesapi.sql_models import sql_model_map
from fidesctl.core.system import generate_aws_systems


class ValidTargets(str, Enum):
    """
    Validation of targets attempted to generate resources from
    """

    AWS = "aws"


class GenerateTypes(str, Enum):
    """
    Generate Type Enum to capture the discrete possible values
    for a valid type of resource to generate.
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


class Generate(BaseModel):
    """
    Defines attributes for generating resources included in a request.
    """

    config: Union[AWSConfig, OktaConfig]
    target: ValidTargets
    type: GenerateTypes

    @root_validator()
    @classmethod
    def target_matches_type(cls, values: Dict) -> Dict:
        """
        Ensures that both of the target and type attributes are a valid
        pair (returning an error on an ('aws', 'dataset') as an example).
        """
        target_type = (values.get("target"), values.get("type"))
        valid_target_types = [("aws", "systems")]
        if target_type not in valid_target_types:
            raise ValueError("Target and Type are not a valid match")
        return values


class GenerateRequestPayload(BaseModel):
    """
    The model for the request body housing generate information.
    """

    organization_key: str
    generate: Generate


class GeneratedResponse(BaseModel):
    """
    The model to house the response for generated infrastructure.
    """

    generate_results: Optional[List[Union[Dataset, System]]]


router = APIRouter(tags=["Generate"], prefix=f"{API_PREFIX}/generate")


@router.post(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=GeneratedResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "content": {
                "application/json": {
                    "example": {"detail": "Unable to generate resources."}
                }
            }
        },
    },
)
async def generate(
    generate_request_payload: GenerateRequestPayload, response: Response
) -> Dict:
    """
    A multi-purpose endpoint to generate Fides resources based on existing
    infrastructure

    Currently generates Fides resources for the following:
    * AWS: Systems

    In the future, this will include options for other Systems & Datasets,
    examples include:
    * Okta: Systems
    * Snowflake: Datasets

    All config secrets should be encoded as a minor security precaution, using the
    `obscure_string` function in `fidesapi.routes.util`

    All production deployments should implement HTTPS for security purposes
    """
    organization = await get_resource(
        sql_model_map["organization"], generate_request_payload.organization_key
    )
    if generate_request_payload.generate.target.lower() == "aws":
        try:
            import boto3  # pylint: disable=unused-import
        except ModuleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Packages not found, ensure aws is included: fidesctl[aws]",
            )
        log.info("Setting config for AWS")
        generated_systems = generate_aws(
            aws_config=AWSConfig(**generate_request_payload.generate.config.dict()),
            organization=organization,
        )
    return {"generate_results": generated_systems}


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
        if error.response["Error"]["Code"] in [
            "InvalidClientTokenId",
            "SignatureDoesNotMatch",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error.response["Error"]["Message"],
            )
        raise error

    return [i.dict(exclude_none=True) for i in aws_systems]
