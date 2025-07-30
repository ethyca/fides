from fastapi import APIRouter, Depends, HTTPException, Security
from loguru import logger
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from fides.api.db.session import get_db
from fides.api.models.privacy_request import RequestTask
from fides.api.schemas.privacy_request import PrivacyRequestResponse
from fides.api.service.async_dsr.async_dsr_service import requeue_polling_request
from fides.api.util.api_router import APIRouter as FidesAPIRouter

router = FidesAPIRouter(
    tags=["Privacy Requests"],
    prefix="/privacy-request",
)


@router.post(
    "/{request_id}/requeue_async",
    status_code=HTTP_200_OK,
    response_model=PrivacyRequestResponse,
    summary="Requeue a polling async privacy request",
)
def requeue_async_request(
    request_id: str,
    db: Session = Depends(get_db),
) -> PrivacyRequestResponse:
    """
    Requeues a polling async privacy request.
    """
    logger.info("Requeuing polling async privacy request with id '{}'", request_id)
    request_task = RequestTask.get(db, object_id=request_id)
    if not request_task:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Request task with id '{request_id}' not found.",
        )
    return requeue_polling_request(db, request_task)
