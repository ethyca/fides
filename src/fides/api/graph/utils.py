from typing import Optional

from fideslang.models import DatasetField


def find_field_by_name(fields: list[DatasetField], name: str) -> Optional[DatasetField]:
    """Find a field by name in a list of dataset fields."""
    for field in fields:
        if field.name == name:
            return field
    return None


def resolve_field_path(
    fields: list[DatasetField], dot_path: str
) -> Optional[DatasetField]:
    """
    Walk nested ``DatasetField.fields`` to find a field by dot-path.

    For example, ``"address.street"`` resolves to the ``street`` sub-field
    inside the ``address`` field.
    """
    parts = dot_path.split(".")
    current_fields = fields
    resolved: Optional[DatasetField] = None
    for part in parts:
        resolved = find_field_by_name(current_fields, part)
        if resolved is None:
            return None
        current_fields = resolved.fields or []
    return resolved
