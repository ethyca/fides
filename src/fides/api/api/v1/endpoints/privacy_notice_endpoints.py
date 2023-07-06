from html import unescape
from typing import Dict, List, Optional, Set, Tuple

from fastapi import Depends, Request, Security
from fastapi_pagination import Page, Params, paginate
from fastapi_pagination.bases import AbstractPage
from loguru import logger
from pydantic import conlist
from sqlalchemy.orm import Query, Session
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.api import deps
from fides.api.common_exceptions import ValidationError
from fides.api.models.privacy_experience import (
    upsert_privacy_experiences_after_notice_update,
)
from fides.api.models.privacy_notice import PrivacyNotice, PrivacyNoticeRegion
from fides.api.models.sql_models import DataUse, System  # type: ignore
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas import privacy_notice as schemas
from fides.api.util.api_router import APIRouter
from fides.api.util.consent_util import (
    PRIVACY_NOTICE_ESCAPE_FIELDS,
    UNESCAPE_SAFESTR_HEADER,
    create_privacy_notices_util,
    ensure_unique_ids,
    prepare_privacy_notice_patches,
    validate_notice_data_uses,
)
from fides.api.util.endpoint_utils import transform_fields
from fides.common.api import scope_registry
from fides.common.api.v1 import urn_registry as urls

router = APIRouter(tags=["Privacy Notice"], prefix=urls.V1_URL_PREFIX)

DataUseMap = Dict[str, List[schemas.PrivacyNoticeResponse]]


def generate_notice_query(
    db: Session,
    show_disabled: Optional[bool] = True,
    systems_applicable: Optional[bool] = False,
    region: PrivacyNoticeRegion = None,
) -> Query:
    """
    Helper function to generate a `PrivacyNotice` query based on certain parameterizations
    """
    notice_query = db.query(PrivacyNotice)
    if not show_disabled:
        notice_query = notice_query.filter(PrivacyNotice.disabled.is_(False))
    if region is not None:
        notice_query = notice_query.filter(PrivacyNotice.regions.contains([region]))
    if systems_applicable:
        data_uses = System.get_data_uses(System.all(db), include_parents=True)
        notice_query = notice_query.filter(PrivacyNotice.data_uses.overlap(data_uses))  # type: ignore
    return notice_query


@router.get(
    urls.PRIVACY_NOTICE,
    status_code=HTTP_200_OK,
    response_model=Page[schemas.PrivacyNoticeResponse],
    dependencies=[
        Security(verify_oauth_client, scopes=[scope_registry.PRIVACY_NOTICE_READ])
    ],
)
def get_privacy_notice_list(
    *,
    db: Session = Depends(deps.get_db),
    params: Params = Depends(),
    show_disabled: Optional[bool] = True,
    region: Optional[PrivacyNoticeRegion] = None,
    systems_applicable: Optional[bool] = False,
    request: Request,
) -> AbstractPage[PrivacyNotice]:
    """
    Return a paginated list of `PrivacyNotice` records in this system.
    Includes some query params to help filter the list if needed
    """
    logger.info("Finding all PrivacyNotices with pagination params '{}'", params)
    notice_query = generate_notice_query(
        db=db,
        show_disabled=show_disabled,
        systems_applicable=systems_applicable,
        region=region,
    )
    should_unescape = request.headers.get(UNESCAPE_SAFESTR_HEADER)
    privacy_notices = notice_query.order_by(PrivacyNotice.created_at.desc())
    return paginate(
        [
            transform_fields(
                transformation=unescape,
                model=notice,
                fields=PRIVACY_NOTICE_ESCAPE_FIELDS,
            )
            if should_unescape
            else notice
            for notice in privacy_notices
        ],
        params=params,
    )


@router.get(
    urls.PRIVACY_NOTICE_BY_DATA_USE,
    status_code=HTTP_200_OK,
    response_model=DataUseMap,
    dependencies=[
        Security(verify_oauth_client, scopes=[scope_registry.PRIVACY_NOTICE_READ])
    ],
)
def get_privacy_notice_by_data_use(*, db: Session = Depends(deps.get_db)) -> DataUseMap:
    """
    Endpoint to retrieve a map of `DataUse`s with their corresponding `PrivacyNotice`s

    Only `DataUse`s that are associated with a `System` are included in the map.

    `DataUse`s that do not have any `PrivacyNotice` associated with them are included
    in the map, with empty lists.
    """

    # get all the data uses associated with a system, and seed our response map
    # with those data uses as keys. no parents returned here since our response map
    # will only have keys corresponding to the the specific data uses associated with systems
    system_data_uses = System.get_data_uses(System.all(db), include_parents=False)
    notices_by_data_use: DataUseMap = {data_use: [] for data_use in system_data_uses}
    # create a lookup table of parent data uses tied to specific data uses for easy lookups later
    data_uses_by_parents: dict[str, str] = {
        parent: data_use
        for data_use in system_data_uses
        for parent in DataUse.get_parent_uses_from_key(data_use)
    }

    # get all notices that are not disabled and share a data use with a system.
    # this includes notices that overlap with parents of data uses associated with systems
    # since those notices do apply to those systems at execution time
    notice_query = generate_notice_query(
        db=db, show_disabled=False, systems_applicable=True
    )
    # for each notice, check each of its data uses, and add it to the
    # corresponding map entry, if it exists. do not create map entries
    # if they don't exist already - the data use is not associated with a system
    for notice in notice_query.all():
        for data_use in notice.data_uses:
            # lookup in our table of parent data uses to get the specific data use
            # that's tied to a system
            system_data_use = data_uses_by_parents.get(data_use, None)
            if system_data_use in notices_by_data_use:
                notices_by_data_use[system_data_use].append(notice)

    return notices_by_data_use


def get_privacy_notice_or_error(db: Session, notice_id: str) -> PrivacyNotice:
    """
    Helper method to load PrivacyNotice or throw a 404
    """
    logger.info("Finding PrivacyNotice with id '{}'", notice_id)
    privacy_notice = PrivacyNotice.get(db=db, object_id=notice_id)
    if not privacy_notice:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"No PrivacyNotice found for id {notice_id}.",
        )

    return privacy_notice


@router.get(
    urls.PRIVACY_NOTICE_DETAIL,
    status_code=HTTP_200_OK,
    response_model=schemas.PrivacyNoticeResponse,
    dependencies=[
        Security(verify_oauth_client, scopes=[scope_registry.PRIVACY_NOTICE_READ])
    ],
)
def get_privacy_notice(
    *,
    privacy_notice_id: str,
    db: Session = Depends(deps.get_db),
    request: Request,
) -> PrivacyNotice:
    """
    Return a single PrivacyNotice
    """
    should_unescape = request.headers.get(UNESCAPE_SAFESTR_HEADER)
    notice = get_privacy_notice_or_error(db, privacy_notice_id)
    if should_unescape:
        notice = transform_fields(
            transformation=unescape,
            model=notice,
            fields=PRIVACY_NOTICE_ESCAPE_FIELDS,
        )  # type: ignore
    return notice


@router.post(
    urls.PRIVACY_NOTICE,
    status_code=HTTP_200_OK,
    response_model=List[schemas.PrivacyNoticeResponse],
    dependencies=[
        Security(verify_oauth_client, scopes=[scope_registry.PRIVACY_NOTICE_CREATE])
    ],
)
def create_privacy_notices(
    *,
    db: Session = Depends(deps.get_db),
    privacy_notices: conlist(schemas.PrivacyNoticeCreation, max_items=50),  # type: ignore
) -> List[PrivacyNotice]:
    """
    Create one or more privacy notices.

    To avoid any confusing or unexpected behavior, the entire operation is void
    if any of the input data does not satisfy validation criteria.
    """
    try:
        created_privacy_notices, _ = create_privacy_notices_util(db, privacy_notices)
    except (ValueError, ValidationError) as e:
        raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return [
        transform_fields(
            transformation=unescape,
            model=notice,
            fields=PRIVACY_NOTICE_ESCAPE_FIELDS,
        )
        for notice in created_privacy_notices
    ]


@router.patch(
    urls.PRIVACY_NOTICE,
    status_code=HTTP_200_OK,
    response_model=List[schemas.PrivacyNoticeResponse],
    dependencies=[
        Security(verify_oauth_client, scopes=[scope_registry.PRIVACY_NOTICE_UPDATE])
    ],
)
def update_privacy_notices(
    *,
    db: Session = Depends(deps.get_db),
    privacy_notice_updates: conlist(schemas.PrivacyNoticeWithId, max_items=50),  # type: ignore
) -> List[PrivacyNotice]:
    """
    Update one or more privacy notices.

    To avoid any confusing or unexpected behavior, the entire operation is void
    if any of the input data does not satisfy validation criteria, or if any
    input privacy notice is not found.
    """
    ensure_unique_ids(privacy_notice_updates)
    validate_notice_data_uses(privacy_notice_updates, db)

    updates_and_existing: List[
        Tuple[schemas.PrivacyNoticeWithId, PrivacyNotice]
    ] = prepare_privacy_notice_patches(  # type: ignore[assignment]
        privacy_notice_updates,
        db,
        PrivacyNotice,
    )

    notices: List[PrivacyNotice] = []
    affected_regions: Set = set()

    for update_data, existing_notice in updates_and_existing:
        existing_notice.update(db, data=update_data.dict(exclude_unset=True))
        notices.append(existing_notice)

        affected_regions.update(existing_notice.regions)

    # After updating all notices, make sure experiences exist to back all notices.
    upsert_privacy_experiences_after_notice_update(
        db, affected_regions=list(affected_regions)
    )

    return [
        transform_fields(
            transformation=unescape,
            model=notice,
            fields=PRIVACY_NOTICE_ESCAPE_FIELDS,
        )
        for notice in notices
    ]
