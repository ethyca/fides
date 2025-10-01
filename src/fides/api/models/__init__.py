from typing import Any, Dict

from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


def update_if_modified(resource: Base, db: Session, *, data: Dict[str, Any]) -> bool:
    """Updates a resource and returns whether it was modified.

    This is used when deciding whether to save a new version for a privacy notice or privacy experience config.
    """
    # run through potential updates
    for key, value in data.items():
        setattr(resource, key, value)

    if db.is_modified(resource):
        resource.save(db)
        return True

    return False


def create_historical_data_from_record(resource: Base) -> Dict:
    """Prep data to be saved in a historical table for record keeping

    This is used when creating a new version for a privacy notice or privacy experience config.
    """
    # Resource attributes are being lazy loaded and not showing up in the dict.  Accessing
    # an attribute causes them to be loaded.
    resource.id  # pylint: disable=pointless-statement
    return clone_object_attributes(resource)


def clone_object_attributes(resource: Base) -> Dict:
    """
    Build a dictionary of the SQLAlchemy-mapped column attributes for this resource.

    Avoid copying the raw __dict__ to prevent cached/computed attributes (e.g.,
    @cached_property) from leaking into historical payloads.
    """
    mapper = sa_inspect(resource.__class__)
    cloned_attributes: Dict = {}

    # Collect only mapped column keys
    for column in mapper.columns:
        key = column.key
        if key in ("id", "created_at", "updated_at"):
            continue
        cloned_attributes[key] = getattr(resource, key)

    return cloned_attributes


def dry_update_data(resource: Base, data_updates: Dict) -> Dict:
    """Copy the record as a dictionary and apply patch updates"""
    # Clone original record
    cloned_attributes: Dict = clone_object_attributes(resource)
    # Replace existing fields with supplied updates
    for key, val in data_updates.items():
        cloned_attributes[key] = val
    return cloned_attributes
