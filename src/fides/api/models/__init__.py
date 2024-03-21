from typing import Any, Dict

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
    Copies an objects attributes into a dictionary.

    Removes protected fields like the SQLAlchemy instance state and id.
    """
    cloned_attributes = resource.__dict__.copy()
    # remove protected fields from the cloned dict
    cloned_attributes.pop("_sa_instance_state", None)
    cloned_attributes.pop("id", None)
    # remove datetime fields
    cloned_attributes.pop("created_at", None)
    cloned_attributes.pop("updated_at", None)
    return cloned_attributes


def dry_update_data(resource: Base, data_updates: Dict) -> Dict:
    """Copy the record as a dictionary and apply patch updates"""
    # Clone original record
    cloned_attributes: Dict = clone_object_attributes(resource)
    # Replace existing fields with supplied updates
    for key, val in data_updates.items():
        cloned_attributes[key] = val
    return cloned_attributes
