from fastapi import Depends, status
from loguru import logger
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from fides.api.analytics import send_registration
from fides.api.api import deps
from fides.api.models.registration import UserRegistration
from fides.api.schemas import registration as schemas
from fides.api.util.api_router import APIRouter
from fides.common.api.v1 import urn_registry as urls

router = APIRouter(
    tags=["Registration"],
    prefix=urls.V1_URL_PREFIX,
)


@router.get(
    urls.REGISTRATION,
    status_code=status.HTTP_200_OK,
    response_model=schemas.GetRegistrationStatusResponse,
)
async def get_registration_status(
    *,
    db: Session = Depends(deps.get_db),
) -> schemas.GetRegistrationStatusResponse:
    """
    Return the registration status of this Fides deployment.
    """
    registrations = UserRegistration.all(db=db)
    if registrations:
        registration = registrations[0]
        opt_in = registration.opt_in
    else:
        opt_in = False

    return schemas.GetRegistrationStatusResponse(opt_in=opt_in)


@router.put(
    urls.REGISTRATION,
    status_code=status.HTTP_200_OK,
    response_model=schemas.Registration,
)
async def update_registration_status(
    *,
    db: Session = Depends(deps.get_db),
    data: schemas.Registration,
) -> UserRegistration:
    """
    Return the registration status of this Fides deployment.
    """
    send_to_fideslog = False
    registrations = UserRegistration.all(db=db)
    if registrations:
        registration = registrations[0]
        if registration.analytics_id != data.analytics_id:
            logger.debug(
                "Error registering Fides with analytics_id: {} to opt_in: {}. Fides with analytics_id: {} already registered.",
                data.analytics_id,
                data.opt_in,
                registration.analytics_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This Fides deployment is already registered.",
            )
    else:
        # If a user registers locally and opts out, don't send data to Fideslog
        send_to_fideslog = data.opt_in

    logger.debug(
        "Registering Fides with analytics_id: {} to opt_in: {}",
        data.analytics_id,
        data.opt_in,
    )
    registration, _ = UserRegistration.create_or_update(  # type: ignore[assignment]
        db=db,
        data=data.model_dump(mode="json"),
    )
    if send_to_fideslog:
        await send_registration(registration)

    return registration
