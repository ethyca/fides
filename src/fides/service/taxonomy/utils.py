from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from fides.api.common_exceptions import ValidationError
from fides.api.db.base_class import get_key_from_data
from fides.api.models.sql_models import (  # type:ignore[attr-defined]
    DataCategory,
    DataSubject,
    DataUse,
)
from fides.api.util.errors import ForbiddenIsDefaultTaxonomyError


# Core validation functions for taxonomy operations
def activate_taxonomy_parents(
    resource: Union[DataCategory, DataUse, DataSubject],
    db: Session,
) -> None:
    """
    Activates parents to match newly-active taxonomy node.
    """
    parent = resource.parent
    if parent:
        parent.active = True
        db.flush()
        activate_taxonomy_parents(parent, db)


def deactivate_taxonomy_node_and_descendants(
    resource: Union[DataCategory, DataUse, DataSubject],
    db: Session,
) -> None:
    """
    Recursively de-activates all descendants of a given taxonomy node.
    """
    resource.active = False
    db.flush()
    children = resource.children

    for child in children:
        # Deactivate current child
        child.active = False
        db.flush()
        # Recursively deactivate all descendants of this child
        deactivate_taxonomy_node_and_descendants(child, db)


def validate_default_taxonomy_restrictions(
    data: Dict,
    resource: Optional[Union[DataCategory, DataUse, DataSubject]] = None,
    action: str = "create",
) -> None:
    """
    Validate restrictions on default taxonomy elements.
    """
    # For creation, check if trying to create with is_default=True
    if action == "create" and data.get("is_default"):
        raise ForbiddenIsDefaultTaxonomyError(
            "taxonomy", data.get("fides_key", "unknown"), action="create"
        )

    # For updates, check if trying to modify is_default field
    if action == "update" and resource:
        # Only check if is_default is explicitly present in the data and is being changed
        if "is_default" in data and hasattr(resource, "is_default"):
            if data["is_default"] != resource.is_default:
                raise ForbiddenIsDefaultTaxonomyError(
                    "resource",
                    data.get("fides_key", resource.fides_key),
                    action="modify",
                )


def validate_parent_key_exists(
    taxonomy_type: str, parent_key: str, handler: Any
) -> None:
    """
    Validate that the parent_key exists in the same taxonomy type.
    This prevents IntegrityError at the database level by validating at application level.
    """
    if not parent_key:
        return

    parent_element = handler.get_element(parent_key)

    if not parent_element:
        raise ValidationError(
            f"Parent with key '{parent_key}' not found in taxonomy '{taxonomy_type}'"
        )


def generate_taxonomy_fides_key(
    taxonomy_type: str,
    name: str,
    parent_key: Optional[str] = None,
    handler: Optional[Any] = None,
) -> str:
    """
    Generate a fides_key from a name for taxonomy elements.
    """
    # Get the actual model class name for key generation
    if handler and hasattr(handler, "get_model"):
        model_class = handler.get_model()
        fides_key = get_key_from_data({"name": name}, model_class.__name__)
    else:
        # Fallback to using taxonomy_type
        fides_key = get_key_from_data({"name": name}, taxonomy_type)

    # Add parent prefix if this is not a root level taxonomy node
    if parent_key:
        fides_key = f"{parent_key}.{fides_key}"

    return fides_key


def check_for_taxonomy_reactivation(
    db: Session, taxonomy_type: str, element_data: Dict, handler: Any
) -> Optional[Any]:
    """
    Check if this is a reactivation case for existing disabled elements.
    Returns the disabled element if it exists and should be reactivated.
    """
    # Only check for reactivation if no fides_key is provided but name is
    if element_data.get("fides_key") or not element_data.get("name"):
        return None

    # Check the specific model table for disabled elements
    model_class = handler.get_model()
    disabled_element = (
        db.query(model_class)
        .filter(
            model_class.active.is_(False),
            model_class.name == element_data["name"],
        )
        .first()
    )
    return disabled_element


def handle_taxonomy_reactivation(
    db: Session, taxonomy_type: str, element: Any, element_data: Dict, handler: Any
) -> Any:
    """
    Handle reactivation of a disabled taxonomy element.
    """
    # Generate fides_key if not provided (needed for reactivation)
    updated_data = element_data.copy()
    if not updated_data.get("fides_key") and updated_data.get("name"):
        updated_data["fides_key"] = generate_taxonomy_fides_key(
            taxonomy_type, updated_data["name"], updated_data.get("parent_key"), handler
        )

    # Ensure it's marked as active and activate parents accordingly
    updated_data["active"] = True
    activate_taxonomy_parents(element, db)

    # Update the element with new data
    element.update(db, data=updated_data)
    return element
