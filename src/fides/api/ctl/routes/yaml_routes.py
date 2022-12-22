from typing import Dict, List, Optional, Tuple

import yaml
from fastapi import HTTPException, Request, Response
from fideslang import Dataset as FideslangDataset
from starlette import status
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_415_UNSUPPORTED_MEDIA_TYPE

from fides.api.ctl.database.crud import create_resource, upsert_resources
from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.sql_models import Dataset  # type: ignore[attr-defined]
from fides.api.ctl.utils.api_router import APIRouter

router = APIRouter(tags=["YAML"], prefix=f"{API_PREFIX}/yml")
X_YAML = "application/x-yaml"


async def parse_dataset_yaml(request: Request) -> List[Dict]:
    """
    Load dataset yaml from the request body
    """
    if request.headers.get("content-type") != X_YAML:
        raise HTTPException(
            status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Supported type: " + X_YAML,
        )
    body = await request.body()

    try:
        yaml_request_body: dict = yaml.safe_load(body)
    except yaml.MarkedYAMLError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Error in YAML: " + str(e)
        )
    datasets: Optional[List[Dict]] = (
        yaml_request_body.get("dataset") if isinstance(yaml_request_body, dict) else []
    )

    if not datasets or len(datasets) == 0:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="No datasets in request body"
        )

    return datasets


@router.post(
    "/dataset",
    response_model=FideslangDataset,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "error": "user does not have permission to modify this resource",
                            "resource_type": "dataset",
                            "fides_key": "example.key",
                        }
                    }
                }
            }
        },
    },
)
async def create(
    request: Request,
) -> Dict:
    """
    Create a Dataset from yaml. Content type must be `application/x-yaml`

    Only one yaml Dataset can be submitted through this endpoint.
    """

    datasets: List[Dict] = await parse_dataset_yaml(request)

    if len(datasets) > 1:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Only one dataset can be submitted through this endpoint",
        )

    return await create_resource(Dataset, FideslangDataset(**datasets[0]).dict())


@router.post(
    "/dataset/upsert",
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": {
                        "message": "Upserted 3 dataset(s)",
                        "inserted": 0,
                        "updated": 3,
                    }
                }
            }
        },
        status.HTTP_201_CREATED: {
            "content": {
                "application/json": {
                    "example": {
                        "message": "Upserted 3 dataset(s)",
                        "inserted": 1,
                        "updated": 2,
                    }
                }
            }
        },
    },
)
async def upsert(
    request: Request,
    response: Response,
) -> Dict:
    """
    Upsert potentially multiple datasets from a yaml request body.
    For any Dataset that already exists in the database,
    update the resource by its `fides_key`. Otherwise, create a new resource.
    Content type must be `application/x-yaml`.

    Responds with a `201 Created` if even a single Dataset
    did not previously exist. Otherwise, responds with a `200 OK`.
    """
    datasets: List[Dict] = await parse_dataset_yaml(request)
    result: Tuple[int, int] = await upsert_resources(Dataset, datasets)
    response.status_code = (
        status.HTTP_201_CREATED if result[0] > 0 else response.status_code
    )

    return {
        "message": f"Upserted {len(datasets)} Datasets(s)",
        "inserted": result[0],
        "updated": result[1],
    }
