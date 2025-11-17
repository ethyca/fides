from typing import Any, Optional

from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import RelationshipProperty

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.task.conditional_dependencies.privacy_request.convenience_fields import (
    build_convenience_field_list,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionalDependencyFieldInfo,
)
from fides.api.task.conditional_dependencies.util import (
    create_conditional_dependency_field_info,
)


def _get_column_type(column: Any) -> str:
    """
    Map SQLAlchemy column type to JSON type string.

    Args:
        column: SQLAlchemy Column object

    Returns:
        JSON type string (e.g., "string", "integer", "boolean")
    """
    column_type = type(column.type).__name__

    # Map SQLAlchemy types to JSON types
    type_mapping = {
        "String": "string",
        "Text": "string",
        "Integer": "integer",
        "BigInteger": "integer",
        "SmallInteger": "integer",
        "Boolean": "boolean",
        "DateTime": "string",  # Datetimes are serialized as strings
        "Date": "string",
        "Time": "string",
        "Float": "float",
        "Numeric": "float",
        "JSON": "object",
        "JSONB": "object",
        "UUID": "string",  # UUIDs are serialized as strings
        "Enum": "string",  # Enums are serialized as strings
        "StringEncryptedType": "string",  # Encrypted types are strings
    }

    # Check for array types
    if "ARRAY" in column_type or "Array" in column_type:
        return "array"

    # Check for encrypted types (they're typically strings)
    if "Encrypted" in column_type:
        return "string"

    # Return mapped type or default to string
    return type_mapping.get(column_type, "string")


def _introspect_orm_model(
    orm_class: type,
    base_path: str,
    fields: list[ConditionalDependencyFieldInfo],
    visited: Optional[set[type]] = None,
    relationship_whitelist: Optional[set[str]] = None,
) -> None:
    """
    Recursively introspect a SQLAlchemy ORM model to extract field information.

    Args:
        orm_class: The SQLAlchemy ORM model class to introspect
        base_path: The base path prefix (e.g., "privacy_request.policy")
        fields: List to append field info to
        visited: Set of already visited model classes to avoid cycles
        relationship_whitelist: Set of relationship names to recurse into (e.g., {"policy"})
    """
    if visited is None:
        visited = set()
    if relationship_whitelist is None:
        relationship_whitelist = set()

    # Avoid infinite recursion on circular references
    if orm_class in visited:
        return

    visited.add(orm_class)

    try:
        mapper = inspect(orm_class)
    except NoInspectionAvailable:
        return

    # Introspect columns
    for column in mapper.columns.values():
        field_path = f"{base_path}.{column.name}" if base_path else column.name
        field_type = _get_column_type(column)
        description = getattr(column, "comment", None)
        fields.append(
            create_conditional_dependency_field_info(
                field_path, field_type, description
            )
        )

    # Introspect relationships
    for relationship_name, relationship_prop in mapper.relationships.items():
        if not isinstance(relationship_prop, RelationshipProperty):
            continue

        field_path = (
            f"{base_path}.{relationship_name}" if base_path else relationship_name
        )

        # Determine if this is a collection (one-to-many, many-to-many) or single (many-to-one, one-to-one)
        is_collection = relationship_prop.uselist

        if is_collection:
            # Collections are arrays - we don't recurse into them
            fields.append(
                create_conditional_dependency_field_info(
                    field_path,
                    "array",
                    f"Relationship to {relationship_prop.entity.class_.__name__} (collection)",
                )
            )
        else:
            # Single relationship - recurse if in whitelist
            target_class = relationship_prop.entity.class_
            fields.append(
                create_conditional_dependency_field_info(
                    field_path,
                    "object",
                    f"Relationship to {target_class.__name__}",
                )
            )

            # Recurse into whitelisted relationships (e.g., policy)
            if relationship_name in relationship_whitelist:
                _introspect_orm_model(
                    target_class,
                    field_path,
                    fields,
                    visited.copy() if visited else None,
                    relationship_whitelist,
                )

    # Add special method-based fields for PrivacyRequest
    if orm_class == PrivacyRequest:
        # identity is a method that returns a dict
        fields.append(
            create_conditional_dependency_field_info(
                f"{base_path}.identity",
                "object",
                "Persisted identity data (email, phone_number, etc.)",
            )
        )
        # custom_privacy_request_fields is a method that returns a dict
        fields.append(
            create_conditional_dependency_field_info(
                f"{base_path}.custom_privacy_request_fields",
                "object",
                "Custom privacy request fields",
            )
        )


def _generate_field_list_from_orm_model(
    orm_class: type,
    base_path: str,
    convenience_fields: Optional[list[ConditionalDependencyFieldInfo]] = None,
    relationship_whitelist: Optional[set[str]] = None,
) -> list[ConditionalDependencyFieldInfo]:
    """
    Generate a list of available fields by introspecting a SQLAlchemy ORM model.

    Args:
        orm_class: The SQLAlchemy ORM model class to introspect
        base_path: The base path prefix (e.g., "privacy_request")
        convenience_fields: Optional list of convenience fields to append
        relationship_whitelist: Set of relationship names to recurse into (e.g., {"policy"})

    Returns:
        List of ConditionalDependencyFieldInfo objects describing available fields
    """
    fields: list[ConditionalDependencyFieldInfo] = []

    # Introspect the ORM model
    _introspect_orm_model(
        orm_class, base_path, fields, relationship_whitelist=relationship_whitelist
    )

    # Add convenience fields if provided
    if convenience_fields:
        fields.extend(convenience_fields)

    return fields


def get_available_privacy_request_fields() -> list[ConditionalDependencyFieldInfo]:
    """
    Generate a list of available fields for privacy request conditional dependencies.

    This function dynamically introspects the SQLAlchemy ORM model to determine
    available fields, and includes convenience fields that are computed from the data.

    Returns:
        List of ConditionalDependencyFieldInfo objects describing available fields
    """
    # Add derived convenience fields
    convenience_fields = build_convenience_field_list()

    # Whitelist relationships to recurse into
    relationship_whitelist = {"policy", "identity", "custom_privacy_request_fields"}

    return _generate_field_list_from_orm_model(
        PrivacyRequest,
        "privacy_request",
        convenience_fields,
        relationship_whitelist=relationship_whitelist,
    )
