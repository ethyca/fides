"""
Contains all of the endpoints required to validate credentials.
"""
from enum import Enum
from typing import Callable, Dict, Union

from fastapi import Response, status
from pydantic import BaseModel

from fides.api.ctl.routes.util import (
    API_PREFIX,
    route_requires_aws_connector,
    route_requires_bigquery_connector,
    route_requires_okta_connector,
)
from fides.api.ctl.utils.api_router import APIRouter
from fides.ctl.connectors.models import (
    AWSConfig,
    BigQueryConfig,
    ConnectorAuthFailureException,
    ConnectorFailureException,
    OktaConfig,
)


class ValidationTarget(str, Enum):
    """
    Allowed targets for the validate endpoint
    """

    AWS = "aws"
    OKTA = "okta"
    BIGQUERY = "bigquery"


class ValidateRequest(BaseModel):
    """
    Validate endpoint request object
    """

    config: Union[AWSConfig, BigQueryConfig, OktaConfig]
    target: ValidationTarget


class ValidationStatus(str, Enum):
    """
    Validate endpoint response status
    """

    SUCCESS = "success"
    FAILURE = "failure"


class ValidateResponse(BaseModel):
    """
    Validate endpoint response object
    """

    status: ValidationStatus
    message: str


router = APIRouter(tags=["Validate"], prefix=f"{API_PREFIX}/validate")


@router.post(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=ValidateResponse,
)
async def validate(
    validate_request_payload: ValidateRequest, response: Response
) -> ValidateResponse:
    """
    Endpoint used to validate different resource targets.
    """
    validate_function_map: Dict[ValidationTarget, Callable] = {
        ValidationTarget.AWS: validate_aws,
        ValidationTarget.BIGQUERY: validate_bigquery,
        ValidationTarget.OKTA: validate_okta,
    }
    validate_function = validate_function_map[validate_request_payload.target]

    try:
        await validate_function(validate_request_payload.config)
    except ConnectorAuthFailureException as err:
        return ValidateResponse(
            status=ValidationStatus.FAILURE,
            message=f"Authentication failed validating config. {str(err)}",
        )
    except ConnectorFailureException as err:
        return ValidateResponse(
            status=ValidationStatus.FAILURE,
            message=f"Unexpected failure validating config. {str(err)}",
        )

    return ValidateResponse(
        status=ValidationStatus.SUCCESS, message="Config validation succeeded"
    )


@route_requires_aws_connector
async def validate_aws(aws_config: AWSConfig) -> None:
    """
    Validates that given aws credentials are valid. Dependency
    exception is raised if failure occurs.
    """
    import fides.ctl.connectors.aws as aws_connector

    aws_connector.validate_credentials(aws_config=aws_config)


@route_requires_bigquery_connector
async def validate_bigquery(bigquery_config: BigQueryConfig) -> None:
    """
    Validates that given GCP BigQuery credentials are valid. Dependency
    exception is raised if failure occurs.
    """
    import fides.ctl.connectors.bigquery as bigquery_connector

    bigquery_engine = bigquery_connector.get_bigquery_engine(bigquery_config)
    bigquery_connector.validate_bigquery_engine(bigquery_engine)


@route_requires_okta_connector
async def validate_okta(okta_config: OktaConfig) -> None:
    """
    Validates that given okta credentials are valid. Dependency
    exception is raised if failure occurs.
    """
    import fides.ctl.connectors.okta as okta_connector

    await okta_connector.validate_credentials(okta_config=okta_config)
