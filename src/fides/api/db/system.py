"""
Functions for interacting with System objects in the database.
"""

import copy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from deepdiff import DeepDiff
from fastapi import HTTPException
from fideslang.models import System as SystemSchema
from fideslang.validation import FidesKey
from loguru import logger as log
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from fides.api.db.crud import create_resource, get_resource, update_resource
from fides.api.models.sql_models import (  # type: ignore[attr-defined]
    DataCategory,
    DataSubject,
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


async def validate_data_labels(
    db: AsyncSession,
    sql_model: Union[Type[DataUse], Type[DataSubject], Type[DataCategory]],
    labels: List[FidesKey],
) -> None:
    """
    Given a model and a list of FidesKeys, check that for each Fides Key
    there is a model instance with that key and the active attribute set to True.
    If any of the keys don't exist or exist but are not active, raise a 400 error
    """
    for label in labels:
        try:
            resource = await get_resource(
                sql_model=sql_model,
                fides_key=label,
                async_session=db,
            )
        except NotFoundError:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Invalid privacy declaration referencing unknown {sql_model.__name__} {label}",
            )

        if not resource.active:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Invalid privacy declaration referencing inactive {sql_model.__name__} {label}",
            )


async def validate_privacy_declarations(db: AsyncSession, system: SystemSchema) -> None:
    """
    Ensure that the `PrivacyDeclaration`s on the provided `System` resource are valid:
     - that they reference valid `DataUse` records
     - that they reference valid `DataCategory` records
     - that they reference valid `DataSubject` records
     - that there are not "duplicate" `PrivacyDeclaration`s as defined by their "logical ID"

    If not, a `400` is raised
    """
    logical_ids = set()
    for privacy_declaration in system.privacy_declarations:
        await validate_data_labels(db, DataUse, [privacy_declaration.data_use])
        await validate_data_labels(
            db, DataCategory, privacy_declaration.data_categories
        )
        await validate_data_labels(db, DataSubject, privacy_declaration.data_subjects)

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
            data = privacy_declaration.model_dump(mode="json")
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

        # delete any existing privacy declarations that have not been "matched" in the request
        for existing_declarations in existing_declarations.values():
            await db.delete(existing_declarations)


async def update_system(
    resource: SystemSchema, db: AsyncSession, current_user_id: Optional[str] = None
) -> Tuple[Dict, bool]:
    """Helper function to share core system update logic for wrapping endpoint functions"""
    system: System = await get_resource(
        sql_model=System, fides_key=resource.fides_key, async_session=db
    )
    existing_system_dict = copy.deepcopy(
        SystemSchema.model_validate(system)
    ).model_dump(mode="json")

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
    updated_system = await update_resource(System, resource.model_dump(), db)

    async with db.begin():

        await db.refresh(updated_system)

        system_updated: bool = _audit_system_changes(
            db,
            system.id,
            current_user_id,
            existing_system_dict,
            SystemSchema.model_validate(updated_system).model_dump(mode="json"),
        )

    return updated_system, system_updated


def _audit_system_changes(
    db: Session,
    system_id: str,
    current_user_id: Optional[str],
    existing_system: Dict[str, Any],
    updated_system: Dict[str, Any],
) -> bool:
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

    system_updated: bool = False

    # Create a SystemHistory entry for general changes
    if DeepDiff(existing_system, updated_system, ignore_order=True):
        system_updated = True

        SystemHistory(
            user_id=current_user_id,
            system_id=system_id,
            before=existing_system,
            after=updated_system,
            created_at=now,
        ).save(db=db)

    # Create a SystemHistory entry for changes to privacy_declarations
    if DeepDiff(privacy_existing, privacy_updated, ignore_order=True):
        system_updated = True

        SystemHistory(
            user_id=current_user_id,
            system_id=system_id,
            before=privacy_existing,
            after=privacy_updated,
            created_at=now,
        ).save(db=db)

    # Create a SystemHistory entry for changes to egress and ingress
    if DeepDiff(egress_ingress_existing, egress_ingress_updated, ignore_order=True):
        system_updated = True

        SystemHistory(
            user_id=current_user_id,
            system_id=system_id,
            before=egress_ingress_existing,
            after=egress_ingress_updated,
            created_at=now,
        ).save(db=db)

    return system_updated


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
    resource_dict = resource.model_dump()

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
                data = privacy_declaration.model_dump(mode="json")
                data["system_id"] = created_system.id  # add FK back to system
                privacy_declaration = PrivacyDeclaration.create(
                    db, data=data
                )  # create the associated PrivacyDeclaration

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
