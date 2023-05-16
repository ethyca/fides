"""
Functions for interacting with System objects in the database.
"""
from typing import Dict, List, Tuple

from fastapi import HTTPException
from fideslang.models import System as SystemSchema
from loguru import logger as log
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from fides.api.ctl.database.crud import (
    get_resource,
    update_resource,
)
from fides.api.ctl.sql_models import (  # type: ignore[attr-defined]
    DataUse,
    PrivacyDeclaration,
    System,
)
from fides.api.ctl.utils.errors import NotFoundError


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
            detail="A valid system must be provided to create or update connections",
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
    resources: List[SystemSchema], db: AsyncSession
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
            await create(resource=resource, db=db)
            inserted += 1
            continue
        await update_system(resource=resource, db=db)
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
            data["system_id"] = system.id  # include FK back to system

            # if we find matching declaration, remove it from our map
            if existing_declaration := existing_declarations.pop(
                privacy_declaration_logical_id(privacy_declaration), None
            ):
                # and update existing declaration *in place*
                existing_declaration.update(db, data=data)
            else:
                # otherwise, create a new declaration record
                PrivacyDeclaration.create(db, data=data)

        # delete any existing privacy declarations that have not been "matched" in the request
        for existing_declarations in existing_declarations.values():
            await db.delete(existing_declarations)


async def update_system(resource: SystemSchema, db: AsyncSession) -> Dict:
    """Helper function to share core system update logic for wrapping endpoint functions"""
    system: System = await get_resource(
        sql_model=System, fides_key=resource.fides_key, async_session=db
    )

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
    return updated_system
