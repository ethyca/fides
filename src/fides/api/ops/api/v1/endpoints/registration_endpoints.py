import logging

from fastapi import Depends, status
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from fides.api.ops.api import deps
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.models.registration import UserRegistration
from fides.api.ops.schemas import registration as schemas
from fides.api.ops.util.api_router import APIRouter

router = APIRouter(
    tags=["Registration"],
    prefix=urls.V1_URL_PREFIX,
)

logger = logging.getLogger(__name__)


@router.get(
    urls.REGISTRATION,
    status_code=status.HTTP_200_OK,
    response_model=schemas.GetRegistrationStatusResponse,
)
def get_registration_status(
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
def update_registration_status(
    *,
    db: Session = Depends(deps.get_db),
    data: schemas.Registration,
) -> schemas.Registration:
    """
    Return the registration status of this Fides deployment.
    """
    registrations = UserRegistration.all(db=db)
    if registrations:
        registration = registrations[0]
        if registration.analytics_id != data.analytics_id:
            logger.debug(
                "Error registering Fides with analytics_id: %s to opt_in: %s. Fides with analytics_id: %s already registered.",
                data.analytics_id,
                data.opt_in,
                registration.analytics_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This Fides deployment is already registered.",
            )

    logger.debug(
        "Registering Fides with analytics_id: %s to opt_in: %s",
        data.analytics_id,
        data.opt_in,
    )
    registration = UserRegistration.create_or_update(
        db=db,
        data=data.dict(),
    )
    return registration
