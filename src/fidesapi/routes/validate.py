"""
Contains all of the endpoints required to validate credentials.
"""
from enum import Enum
from typing import Callable, Dict, Union

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel

from fidesapi.routes.util import API_PREFIX
from fidesctl.connectors.models import AWSConfig, OktaConfig


class ValidationTarget(str, Enum):
    """
    TODO
    """

    AWS = "aws"
    OKTA = "okta"


class ValidateRequest(BaseModel):
    """
    TODO
    """

    config: Union[AWSConfig, OktaConfig]
    target: ValidationTarget


class ValidationStatus(str, Enum):
    """
    TODO
    """

    SUCCESS = "success"
    FAILURE = "failure"


class ValidateResponse(BaseModel):
    """
    TODO
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
) -> Dict:
    """
    TODO
    """
    validate_function_map: Dict[ValidationTarget, Callable] = {
        ValidationTarget.AWS: validate_aws
    }
    validate_function = validate_function_map[ValidationTarget.AWS]
    validate_response = validate_function(validate_request_payload.config)
    return validate_response.dict()


def validate_aws(aws_config: AWSConfig) -> ValidateResponse:
    """
    Validates that given credentials are valid and builds a response
    """
    try:
        import boto3  # pylint: disable=unused-import
    except ModuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Packages not found, ensure aws is included: fidesctl[aws]",
        )
    return ValidateResponse(
        status=ValidationStatus.SUCCESS, message="Config validation succeeded"
    )
