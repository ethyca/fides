"""
Contains all of the endpoints required to manage generating resources.
"""

from enum import Enum
from typing import Dict, List, Optional, Union

from fastapi import Depends, HTTPException, Security, status
from fideslang.models import Dataset, Organization, System
from loguru import logger as log
from pydantic import BaseModel, root_validator
from sqlalchemy.ext.asyncio import AsyncSession

from fides.api.api.v1.endpoints import API_PREFIX
from fides.api.db.crud import get_resource
from fides.api.db.ctl_session import get_async_db
from fides.api.models.sql_models import sql_model_map  # type: ignore[attr-defined]
from fides.api.oauth.utils import verify_oauth_client_prod
from fides.api.util.api_router import APIRouter
from fides.common.api import scope_registry
from fides.connectors.models import (
    AWSConfig,
    BigQueryConfig,
    ConnectorAuthFailureException,
    ConnectorFailureException,
    DatabaseConfig,
    OktaConfig,
)
from fides.core.dataset import (
    generate_bigquery_datasets,
    generate_db_datasets,
    generate_dynamo_db_datasets,
)
from fides.core.system import generate_aws_systems, generate_okta_systems
from fides.core.utils import validate_db_engine

GENERATE_ROUTER = APIRouter(tags=["Generate"], prefix=f"{API_PREFIX}/generate")


class ValidTargets(str, Enum):
    """
    Validation of targets attempted to generate resources from
    """

    AWS = "aws"
    DB = "db"
    OKTA = "okta"
    BIGQUERY = "bigquery"
    DYNAMODB = "dynamodb"


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

    config: Union[AWSConfig, OktaConfig, DatabaseConfig, BigQueryConfig]
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
        valid_target_types = [
            ("aws", "systems"),
            ("bigquery", "datasets"),
            ("db", "datasets"),
            ("dynamodb", "datasets"),
            ("okta", "systems"),
        ]
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


@GENERATE_ROUTER.post(
    "/",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Security(verify_oauth_client_prod, scopes=[scope_registry.GENERATE_EXEC])
    ],
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
    generate_request_payload: GenerateRequestPayload,
    db: AsyncSession = Depends(get_async_db),
) -> GenerateResponse:
    """
    A multi-purpose endpoint to generate Fides resources based on existing
    infrastructure

    Currently generates Fides resources for the following:
    * AWS: Systems
    * Okta: Systems
    * DB: Datasets
    * BigQuery: Datasets
    * DynamoDB: Datasets

    In the future, this will include options for other Systems & Datasets,
    examples include:
    * Snowflake: Datasets

    All production deployments should implement HTTPS for security purposes
    """
    organization = await get_resource(
        sql_model_map["organization"], generate_request_payload.organization_key, db
    )
    generate_config = generate_request_payload.generate.config
    generate_target = generate_request_payload.generate.target.lower()
    try:
        if generate_target == "aws" and isinstance(generate_config, AWSConfig):
            generate_results = generate_aws(
                aws_config=generate_config,
                organization=organization,
            )

        elif generate_target == "db" and isinstance(generate_config, DatabaseConfig):
            generate_results = generate_db(
                db_config=generate_config,
            )

        elif generate_target == "okta" and isinstance(generate_config, OktaConfig):
            generate_results = await generate_okta(
                okta_config=generate_config,
                organization=organization,
            )

        elif generate_target == "bigquery" and isinstance(
            generate_config, BigQueryConfig
        ):
            generate_results = generate_bigquery(
                bigquery_config=generate_config,
            )

        elif generate_target == "dynamodb" and isinstance(generate_config, AWSConfig):
            generate_results = generate_dynamodb(
                aws_config=generate_config,
                organization=organization,
            )

    except ConnectorAuthFailureException as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )

    return GenerateResponse(generate_results=generate_results)


def generate_aws(
    aws_config: AWSConfig, organization: Organization
) -> List[Dict[str, str]]:
    """
    Returns a list of Systems found in AWS.
    """
    from fides.connectors.aws import validate_credentials

    log.info("Validating AWS credentials")
    try:
        validate_credentials(aws_config)
    except ConnectorAuthFailureException as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        )

    log.info("Generating systems from AWS")
    aws_systems = generate_aws_systems(organization=organization, aws_config=aws_config)

    return [i.dict(exclude_none=True) for i in aws_systems]


def generate_dynamodb(
    aws_config: AWSConfig, organization: Organization
) -> List[Dict[str, str]]:
    """
    Returns a list of DynamoDB datasets found in AWS.
    """
    from fides.connectors.aws import validate_credentials

    log.info("Validating AWS credentials")
    try:
        validate_credentials(aws_config)
    except ConnectorAuthFailureException as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        )

    log.info("Generating datasets from AWS DynamoDB")
    aws_resources = [generate_dynamo_db_datasets(aws_config=aws_config)]

    return [i.dict(exclude_none=True) for i in aws_resources]


async def generate_okta(
    okta_config: OktaConfig, organization: Organization
) -> List[Dict[str, str]]:
    """
    Returns a list of Systems found in Okta.
    """
    from fides.connectors.okta import validate_credentials

    log.info("Validating Okta credentials")
    try:
        validate_credentials(okta_config)
    except ConnectorAuthFailureException as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        )
    log.info("Generating systems from Okta")
    okta_systems = await generate_okta_systems(
        organization=organization, okta_config=okta_config
    )
    return [i.dict(exclude_none=True) for i in okta_systems]


def generate_db(db_config: DatabaseConfig) -> List[Dict[str, str]]:
    """
    Returns a list of datasets found in a database.
    """
    log.info("Validating database credentials")
    try:
        validate_db_engine(db_config.connection_string)
    except ConnectorAuthFailureException as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        )
    log.info("Generating datasets from database")
    db_datasets = generate_db_datasets(connection_string=db_config.connection_string)

    return [i.dict(exclude_none=True) for i in db_datasets]


def generate_bigquery(bigquery_config: BigQueryConfig) -> List[Dict[str, str]]:
    """
    Returns a list of datasets found in a BigQuery dataset
    """
    log.info("Generating datasets from BigQuery")
    try:
        bigquery_datasets = generate_bigquery_datasets(bigquery_config)
    except ConnectorFailureException as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        )
    return [i.dict(exclude_none=True) for i in bigquery_datasets]
