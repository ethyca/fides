from typing import Dict, List, Optional, Tuple

from fastapi import Depends, Security
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from loguru import logger
from pydantic import conlist
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from fides.api.ctl.sql_models import DataUse, System  # type: ignore
from fides.api.ops.api import deps
from fides.api.ops.api.v1 import scope_registry
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.common_exceptions import ValidationError
from fides.api.ops.models.privacy_notice import (
    PrivacyNotice,
    PrivacyNoticeRegion,
    check_conflicting_data_uses,
)
from fides.api.ops.schemas import privacy_notice as schemas
from fides.api.ops.util.api_router import APIRouter
from fides.api.ops.util.oauth_util import verify_oauth_client

router = APIRouter(tags=["Privacy Notice"], prefix=urls.V1_URL_PREFIX)


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
) -> AbstractPage[PrivacyNotice]:
    """
    Return a paginated list of PrivacyNotice records in this system.
    Includes some query params to help filter the list if needed
    """
    logger.info("Finding all PrivacyNotices with pagination params '{}'", params)
    notice_query = db.query(PrivacyNotice)
    if not show_disabled:
        notice_query = notice_query.filter(PrivacyNotice.disabled.is_(False))
    if region is not None:
        notice_query = notice_query.filter(PrivacyNotice.regions.contains([region]))
    if systems_applicable:
        data_uses = System.get_system_data_uses(db)
        notice_query = notice_query.filter(PrivacyNotice.data_uses.overlap(data_uses))  # type: ignore
    privacy_notices = notice_query.order_by(PrivacyNotice.created_at.desc())
    return paginate(privacy_notices, params=params)


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
) -> PrivacyNotice:
    """
    Return a single PrivacyNotice
    """
    return get_privacy_notice_or_error(db, privacy_notice_id)  # type: ignore[return-value]


def validate_notice_data_uses(
    privacy_notices: List[schemas.PrivacyNotice],
    db: Session,
) -> None:
    """
    Ensures that all the provided `PrivacyNotice`s have valid data uses.
    Raises a 422 HTTP exception if an unknown data use is found on any `PrivacyNotice`
    """
    valid_data_uses = [data_use.fides_key for data_use in DataUse.query(db).all()]
    try:
        for privacy_notice in privacy_notices:
            privacy_notice.validate_data_uses(valid_data_uses)
    except ValueError as e:
        raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


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
    validate_notice_data_uses(privacy_notices, db)

    existing_notices = (
        PrivacyNotice.query(db).filter(PrivacyNotice.disabled.is_(False)).all()
    )

    new_notices = [
        PrivacyNotice(**privacy_notice.dict(exclude_unset=True))
        for privacy_notice in privacy_notices
    ]
    try:
        check_conflicting_data_uses(new_notices, existing_notices)
    except ValidationError as e:
        raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)

    return [
        PrivacyNotice.create(
            db=db, data=privacy_notice.dict(exclude_unset=True), check_name=False
        )
        for privacy_notice in privacy_notices
    ]


def prepare_privacy_notice_patches(
    privacy_notice_updates: List[schemas.PrivacyNoticeWithId],
    db: Session,
) -> List[Tuple[schemas.PrivacyNoticeWithId, PrivacyNotice]]:
    """
    Prepares our privacy notice patch updates,
    including performing data use conflict validation on proposed patch updates.

    Returns a list of tuples that have the PrivacyNotice update data (API schema) alongside
    their associated existing PrivacyNotice db record that will be updated
    """

    # first we populate a map of privacy notices in the db, indexed by ID
    existing_notices: Dict[str, PrivacyNotice] = {}
    for existing_notice in PrivacyNotice.query(db).all():
        existing_notices[existing_notice.id] = existing_notice

    # then associate existing notices with their updates
    # we'll return this set of data to actually process updates
    updates_and_existing: List[Tuple[schemas.PrivacyNoticeWithId, PrivacyNotice]] = []
    for update_data in privacy_notice_updates:
        if update_data.id not in existing_notices:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"No PrivacyNotice found for id {update_data.id}.",
            )

        updates_and_existing.append((update_data, existing_notices[update_data.id]))

    # we temporarily store proposed update data in-memory for validation purposes only
    validation_updates = []
    for (update_data, existing_notice) in updates_and_existing:
        # add the patched update to our temporary updates for validation
        validation_updates.append(
            existing_notice.dry_update(data=update_data.dict(exclude_unset=True))
        )
        # and don't include it anymore in the existing notices used for validation
        existing_notices.pop(existing_notice.id, None)

    # run the validation here on our proposed "dry-run" updates
    try:
        check_conflicting_data_uses(validation_updates, existing_notices.values())
    except ValidationError as e:
        raise HTTPException(HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)

    # return the tuples of update data associated with their existing db records
    return updates_and_existing


def ensure_unique_ids(
    privacy_notices: List[schemas.PrivacyNoticeWithId],
) -> None:
    """
    Ensures that all the provided `PrivacyNotice`s have unique IDs
    Raises a 422 HTTP exception if there is more than one PrivacyNotice with the same ID
    """
    ids = set()
    for privacy_notice in privacy_notices:
        if privacy_notice.id not in ids:
            ids.add(privacy_notice.id)
        else:
            raise HTTPException(
                HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"More than one provided PrivacyNotice with ID {privacy_notice.id}.",
            )


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
    ] = prepare_privacy_notice_patches(privacy_notice_updates, db)
    return [
        existing_notice.update(db, data=update_data.dict(exclude_unset=True))
        for (update_data, existing_notice) in updates_and_existing
    ]
