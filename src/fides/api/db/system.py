"""
Functions for interacting with System objects in the database.
"""
import copy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from deepdiff import DeepDiff
from fastapi import HTTPException
from fideslang.models import Cookies as CookieSchema
from fideslang.models import System as SystemSchema
from loguru import logger as log
from sqlalchemy import and_, delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from fides.api.db.crud import create_resource, get_resource, update_resource
from fides.api.models.sql_models import (  # type: ignore[attr-defined]
    Cookies,
    DataUse,
    PrivacyDeclaration,
    System,
)
from fides.api.models.system_history import SystemHistory
from fides.api.util.errors import NotFoundError


def privacy_declaration_logical_id(
    privacy_declaration: PrivacyDeclaration,
) -> str:
    """
    Helper to standardize a logical 'id' for privacy declarations.
    As of now, this is based on the `data_use` and the `name` of the declaration, if provided.
    """
    return f"{privacy_declaration.data_use}:{privacy_declaration.name or ''}"


def get_system(db: Session, fides_key: str) -> System:
    system = System.get_by(db, field="fides_key", value=fides_key)
    if system is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="The specified system was not found. Please provide a valid system for the requested operation.",
        )
    return system


async def validate_privacy_declarations(db: AsyncSession, system: SystemSchema) -> None:
    """
    Ensure that the `PrivacyDeclaration`s on the provided `System` resource are valid:
     - that they reference valid `DataUse` records
     - that there are not "duplicate" `PrivacyDeclaration`s as defined by their "logical ID"

    If not, a `400` is raised
    """
    logical_ids = set()
    for privacy_declaration in system.privacy_declarations:
        try:
            await get_resource(
                sql_model=DataUse,
                fides_key=privacy_declaration.data_use,
                async_session=db,
            )
        except NotFoundError:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Invalid privacy declaration referencing unknown DataUse {privacy_declaration.data_use}",
            )
        logical_id = privacy_declaration_logical_id(privacy_declaration)
        if logical_id in logical_ids:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Duplicate privacy declarations specified with data use {privacy_declaration.data_use}",
            )

        logical_ids.add(logical_id)


async def upsert_system(
    resources: List[SystemSchema],
    db: AsyncSession,
    current_user_id: Optional[str] = None,
) -> Tuple[int, int]:
    """Helper method to abstract system upsert logic from API code"""
    inserted = 0
    updated = 0
    # first pass to validate privacy declarations before proceeding
    for resource in resources:
        await validate_privacy_declarations(db, resource)

    for resource in resources:
        try:
            await get_resource(System, resource.fides_key, db)
        except NotFoundError:
            log.debug(
                f"Upsert System with fides_key {resource.fides_key} not found, will create"
            )
            await create_system(
                resource=resource, db=db, current_user_id=current_user_id
            )
            inserted += 1
            continue
        await update_system(resource=resource, db=db, current_user_id=current_user_id)
        updated += 1
    return (inserted, updated)


async def upsert_privacy_declarations(
    db: AsyncSession, resource: SystemSchema, system: System
) -> None:
    """Helper to handle the specific upsert logic for privacy declarations"""

    async with db.begin():
        # map existing declarations by their logical identifier
        existing_declarations: Dict[str, PrivacyDeclaration] = {
            privacy_declaration_logical_id(existing_declaration): existing_declaration
            for existing_declaration in system.privacy_declarations
        }

        # iterate through declarations specified on the request and upsert
        # looking for "matching" existing declarations based on data_use and name
        for privacy_declaration in resource.privacy_declarations:
            # prepare our 'payload' for either create or update
            data = privacy_declaration.dict()
            cookies: List[Dict] = data.pop("cookies", None)
            data["system_id"] = system.id  # include FK back to system

            # if we find matching declaration, remove it from our map
            if declaration := existing_declarations.pop(
                privacy_declaration_logical_id(privacy_declaration), None
            ):
                # and update existing declaration *in place*
                declaration.update(db, data=data)
            else:
                # otherwise, create a new declaration record
                declaration = PrivacyDeclaration.create(db, data=data)

            # Upsert cookies for the given privacy declaration
            await upsert_cookies(db, cookies, declaration, system)

        # delete any existing privacy declarations that have not been "matched" in the request
        for existing_declarations in existing_declarations.values():
            await db.delete(existing_declarations)


async def upsert_cookies(
    async_session: AsyncSession,
    cookies: Optional[List[Dict]],
    privacy_declaration: PrivacyDeclaration,
    system: System,
) -> None:
    """
    Upsert cookies for the given privacy declaration: retrieve cookies
    by name/system/privacy declaration.

    Remove any existing cookies that aren't specified here.
    """

    parsed_cookies = (
        [CookieSchema.parse_obj(cookie) for cookie in cookies] if cookies else []
    )

    for cookie_data in parsed_cookies:
        # Check if cookie exists for this name/system/privacy declaration
        result = await async_session.execute(
            select(Cookies).where(
                and_(
                    Cookies.name == cookie_data.name,
                    Cookies.system_id == system.id,
                    Cookies.privacy_declaration_id == privacy_declaration.id,
                )
            )
        )
        row: Optional[Cookies] = result.scalars().first()
        if row:
            await async_session.execute(
                update(Cookies).where(Cookies.id == row.id).values(cookie_data.dict())
            )

        else:
            await async_session.execute(
                insert(Cookies).values(
                    {
                        "name": cookie_data.name,
                        "path": cookie_data.path,
                        "domain": cookie_data.domain,
                        "privacy_declaration_id": privacy_declaration.id,
                        "system_id": system.id,
                    }
                )
            )

    # Select cookies which are currently on the privacy declaration but not included in this request
    delete_result = await async_session.execute(
        select(Cookies).where(
            and_(
                Cookies.name.notin_([cookie.name for cookie in parsed_cookies]),
                Cookies.system_id == system.id,
                Cookies.privacy_declaration_id == privacy_declaration.id,
            )
        )
    )

    # Remove those cookies altogether
    await async_session.execute(
        delete(Cookies).where(
            Cookies.id.in_(
                [cookie.id for cookie in delete_result.scalars().unique().all()]
            )
        )
    )


async def update_system(
    resource: SystemSchema, db: AsyncSession, current_user_id: Optional[str] = None
) -> Dict:
    """Helper function to share core system update logic for wrapping endpoint functions"""
    system: System = await get_resource(
        sql_model=System, fides_key=resource.fides_key, async_session=db
    )
    existing_system_dict = copy.deepcopy(SystemSchema.from_orm(system).dict())

    # handle the privacy declaration upsert logic
    try:
        await upsert_privacy_declarations(db, resource, system)
    except Exception as e:
        log.error(
            f"Error adding privacy declarations, reverting system creation: {str(e)}"
        )
        raise e

    delattr(
        resource, "privacy_declarations"
    )  # remove the attribute on the system since we've already updated declarations

    # perform any updates on the system resource itself
    updated_system = await update_resource(System, resource.dict(), db)
    async with db.begin():
        await db.refresh(updated_system)
        _audit_system_changes(
            db,
            system.id,
            current_user_id,
            existing_system_dict,
            SystemSchema.from_orm(updated_system).dict(),
        )

    return updated_system


def _audit_system_changes(
    db: Session,
    system_id: str,
    current_user_id: Optional[str],
    existing_system: Dict[str, Any],
    updated_system: Dict[str, Any],
) -> None:
    """
    Audits changes made to a system and logs them in the SystemHistory table.
    The function creates separate SystemHistory entries for general changes,
    changes to privacy declarations (data uses), and changes to egress and ingress (data flow) settings.
    This is done to match the way the user interacts with the system from the UI.
    """

    # Extract egress, ingress, and privacy_declarations fields
    egress_ingress_existing = {
        field: existing_system.pop(field, None) for field in ["egress", "ingress"]
    }
    egress_ingress_updated = {
        field: updated_system.pop(field, None) for field in ["egress", "ingress"]
    }
    privacy_existing = {
        "privacy_declarations": existing_system.pop("privacy_declarations", [])
    }
    privacy_updated = {
        "privacy_declarations": updated_system.pop("privacy_declarations", [])
    }

    # Get the current datetime
    now = datetime.now()

    # Create a SystemHistory entry for general changes
    if DeepDiff(existing_system, updated_system, ignore_order=True):
        SystemHistory(
            user_id=current_user_id,
            system_id=system_id,
            before=existing_system,
            after=updated_system,
            created_at=now,
        ).save(db=db)

    # Create a SystemHistory entry for changes to privacy_declarations
    if DeepDiff(privacy_existing, privacy_updated, ignore_order=True):
        SystemHistory(
            user_id=current_user_id,
            system_id=system_id,
            before=privacy_existing,
            after=privacy_updated,
            created_at=now,
        ).save(db=db)

    # Create a SystemHistory entry for changes to egress and ingress
    if DeepDiff(egress_ingress_existing, egress_ingress_updated, ignore_order=True):
        SystemHistory(
            user_id=current_user_id,
            system_id=system_id,
            before=egress_ingress_existing,
            after=egress_ingress_updated,
            created_at=now,
        ).save(db=db)


async def create_system(
    resource: SystemSchema, db: AsyncSession, current_user_id: Optional[str] = None
) -> Dict:
    """
    Override `System` create/POST to handle `.privacy_declarations` defined inline,
    for backward compatibility and ease of use for API users.
    """
    await validate_privacy_declarations(db, resource)
    # copy out the declarations to be stored separately
    # as they will be processed AFTER the system is added
    privacy_declarations = resource.privacy_declarations

    # remove the attribute on the system update since the declarations will be created separately
    delattr(resource, "privacy_declarations")

    # create the system resource using generic creation
    # the system must be created before the privacy declarations so that it can be referenced
    resource_dict = resource.dict()

    # set the current user's ID
    resource_dict["user_id"] = current_user_id

    created_system = await create_resource(
        System, resource_dict=resource_dict, async_session=db
    )

    privacy_declaration_exception = None
    try:
        async with db.begin():
            # create the specified declarations as records in their own table
            for privacy_declaration in privacy_declarations:
                data = privacy_declaration.dict()
                data["system_id"] = created_system.id  # add FK back to system
                cookies: List[Dict] = data.pop("cookies", [])
                privacy_declaration = PrivacyDeclaration.create(
                    db, data=data
                )  # create the associated PrivacyDeclaration
                await upsert_cookies(
                    db, cookies, privacy_declaration, created_system
                )  # Create the associated cookies
    except Exception as e:
        log.error(
            f"Error adding privacy declarations, reverting system creation: {str(privacy_declaration_exception)}"
        )
        async with db.begin():
            await db.delete(created_system)
        raise e

    async with db.begin():
        await db.refresh(created_system)

    return created_system
