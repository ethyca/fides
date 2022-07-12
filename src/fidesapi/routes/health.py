from typing import Dict

from fastapi import HTTPException, status

import fidesctl
from fidesapi.database.database import get_db_health
from fidesapi.routes.util import API_PREFIX
from fidesapi.utils.api_router import APIRouter
from fidesctl.core.config import FidesctlConfig, get_config

CONFIG: FidesctlConfig = get_config()

router = APIRouter(prefix=API_PREFIX, tags=["Health"])


@router.get(
    "/health",
    response_model=Dict[str, str],
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "database": "healthy",
                    }
                }
            }
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "healthy",
                            "version": "1.0.0",
                            "database": "unhealthy",
                        }
                    }
                }
            }
        },
    },
)
async def health() -> Dict:
    "Confirm that the API is running and healthy."
    database_health = get_db_health(CONFIG.api.sync_database_url)
    response = {
        "status": "healthy",
        "version": str(fidesctl.__version__),
        "database": database_health,
    }

    for key in response:
        if response[key] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response
            )

    return response
