"""
Contains all of the endpoints required to manage a scan of your resources.
"""
from enum import Enum
from typing import Dict

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from fidesapi.utils.helpers import unobscure


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


router = APIRouter(tags=["scan"], prefix="/scan")

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
    """
    response.status_code = status.HTTP_201_CREATED
    scan_resource.scan_config["aws_secret_key"] = unobscure(
        scan_resource.scan_config["aws_secret_key"]
    ).decode()
    return scan_resource.dict()
