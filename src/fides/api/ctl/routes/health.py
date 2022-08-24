from typing import Dict

from fastapi import HTTPException, status

import fidesctl
from fides.api.ctl.database.database import get_db_health
from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.utils.api_router import APIRouter
from fides.ctl.core.config import FidesctlConfig, get_config

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
    database_health = get_db_health(CONFIG.database.sync_database_uri)
    response = {
        "status": "healthy",
        "version": str(fidesctl.__version__),
        "database": database_health,
    }

    for _, value in response.items():
        if value == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response
            )

    return response
