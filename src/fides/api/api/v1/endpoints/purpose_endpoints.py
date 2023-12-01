from fastapi import Depends, Security
from fideslang.gvl import MAPPED_PURPOSES, MAPPED_SPECIAL_PURPOSES
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK

from fides.api.api import deps
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.tcf import PurposesResponse
from fides.api.util.api_router import APIRouter
from fides.common.api.v1 import urn_registry as urls

router = APIRouter(tags=["Purposes"], prefix=urls.V1_URL_PREFIX)


@router.get(
    "/purposes",
    dependencies=[Security(verify_oauth_client)],
    status_code=HTTP_200_OK,
    response_model=PurposesResponse,
)
def get_purposes(
    db: Session = Depends(deps.get_db),
) -> PurposesResponse:
    """
    Return a map of purpose and special purpose IDs to mapped purposes which include data uses.
    """

    purposes = {}
    special_purposes = {}
    for purpose in MAPPED_PURPOSES.values():
        purposes[purpose.id] = purpose
    for special_purpose in MAPPED_SPECIAL_PURPOSES.values():
        special_purposes[special_purpose.id] = special_purpose
    return PurposesResponse(purposes=purposes, special_purposes=special_purposes)
