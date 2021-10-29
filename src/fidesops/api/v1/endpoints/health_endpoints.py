from typing import Any, Dict

from fastapi import APIRouter


router = APIRouter(tags=["Public"])


@router.get("/health", response_model=Dict[str, bool])
def health_check() -> Dict[str, bool]:
    return {
        "healthy": True,
    }
