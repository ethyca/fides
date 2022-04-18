from typing import Dict

from fastapi import APIRouter

from fidesops.api.v1.urn_registry import HEALTH

router = APIRouter(tags=["Public"])


@router.get(HEALTH, response_model=Dict[str, bool])
def health_check() -> Dict[str, bool]:
    return {
        "healthy": True,
    }
