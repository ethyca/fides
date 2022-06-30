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
from fidesapi.routes.util import API_PREFIX, route_requires_aws_connector
from fidesapi.sql_models import sql_model_map
from fidesctl.connectors.models import (
    AWSConfig,
    ConnectorAuthFailureException,
    OktaConfig,
)
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


class GenerateResponse(BaseModel):
    """
    The model to house the response for generated infrastructure.
    """

    generate_results: Optional[List[Union[Dataset, System]]]


router = APIRouter(tags=["Generate"], prefix=f"{API_PREFIX}/generate")


@router.post(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=GenerateResponse,
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
) -> GenerateResponse:
    """
    A multi-purpose endpoint to generate Fides resources based on existing
    infrastructure

    Currently generates Fides resources for the following:
    * AWS: Systems

    In the future, this will include options for other Systems & Datasets,
    examples include:
    * Okta: Systems
    * Snowflake: Datasets

    All production deployments should implement HTTPS for security purposes
    """
    organization = await get_resource(
        sql_model_map["organization"], generate_request_payload.organization_key
    )
    if generate_request_payload.generate.target.lower() == "aws":
        generated_systems = generate_aws(
            aws_config=AWSConfig(**generate_request_payload.generate.config.dict()),
            organization=organization,
        )
    return GenerateResponse(generate_results=generated_systems)


@route_requires_aws_connector
def generate_aws(
    aws_config: AWSConfig, organization: Organization
) -> List[Dict[str, str]]:
    """
    Returns a list of Systems found in AWS.
    """
    log.info("Setting config for AWS")
    try:
        log.info("Generating systems from AWS")
        aws_systems = generate_aws_systems(
            organization=organization, aws_config=aws_config
        )
    except ConnectorAuthFailureException as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )

    return [i.dict(exclude_none=True) for i in aws_systems]
