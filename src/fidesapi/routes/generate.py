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
from fidesapi.routes.util import (
    API_PREFIX,
    route_requires_aws_connector,
    route_requires_okta_connector,
)
from fidesapi.sql_models import sql_model_map
from fidesctl.connectors.models import (
    AWSConfig,
    ConnectorAuthFailureException,
    DatabaseConfig,
    OktaConfig,
)
from fidesctl.core.dataset import generate_db_datasets
from fidesctl.core.system import generate_aws_systems, generate_okta_systems


class ValidTargets(str, Enum):
    """
    Validation of targets attempted to generate resources from
    """

    AWS = "aws"
    DB = "db"
    OKTA = "okta"


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

    config: Union[AWSConfig, OktaConfig, DatabaseConfig]
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
        valid_target_types = [("aws", "systems"), ("okta", "systems"), ("db", "datasets")]
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
    * Okta: Systems

    In the future, this will include options for other Systems & Datasets,
    examples include:
    * Snowflake: Datasets

    All production deployments should implement HTTPS for security purposes
    """
    organization = await get_resource(
        sql_model_map["organization"], generate_request_payload.organization_key
    )
    try:
        if generate_request_payload.generate.target.lower() == "aws":
            generate_results = generate_aws(
                aws_config=AWSConfig(**generate_request_payload.generate.config.dict()),
                organization=organization,
            )
        elif generate_request_payload.generate.target.lower() == "db":
            generate_results = generate_db(
                db_config=generate_request_payload.generate.config,
                aws_config=generate_request_payload.generate.config,
                organization=organization,
            )
        elif generate_request_payload.generate.target.lower() == "okta":
            generate_results = await generate_okta(
                okta_config=generate_request_payload.generate.config,
                organization=organization,
            )
    except ConnectorAuthFailureException as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )
    return GenerateResponse(generate_results=generate_results)


@route_requires_aws_connector
def generate_aws(
    aws_config: AWSConfig, organization: Organization
) -> List[Dict[str, str]]:
    """
    Returns a list of Systems found in AWS.
    """
    log.info("Generating systems from AWS")
    aws_systems = generate_aws_systems(organization=organization, aws_config=aws_config)

    return [i.dict(exclude_none=True) for i in aws_systems]

@route_requires_okta_connector
async def generate_okta(
    okta_config: OktaConfig, organization: Organization
) -> List[Dict[str, str]]:
    """
    Returns a list of Systems found in Okta.
    """
    log.info("Generating systems from Okta")
    okta_systems = await generate_okta_systems(
        organization=organization, okta_config=okta_config
    )
    return [i.dict(exclude_none=True) for i in okta_systems]

def generate_db(db_config: DatabaseConfig) -> List[Dict[str, str]]:
    """
    Returns a list of datasets found in a database.
    """
    log.info("Generating datasets from database")
    db_datasets = generate_db_datasets(connection_string=db_config.connection_string)

    return [i.dict(exclude_none=True) for i in db_datasets]
