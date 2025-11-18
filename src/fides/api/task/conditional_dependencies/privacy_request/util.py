from typing import Any, Optional

from loguru import logger
from pydantic.v1.utils import deep_update
from sqlalchemy.orm import Session

from fides.api.models.privacy_center_config import (
    PrivacyCenterConfig as PrivacyCenterConfigModel,
)
from fides.api.models.property import Property
from fides.api.schemas.privacy_center_config import (
    PrivacyCenterConfig as PrivacyCenterConfigSchema,
)
from fides.api.schemas.privacy_center_config import PrivacyRequestOption
from fides.api.task.conditional_dependencies.privacy_request.convenience_fields import (
    build_convenience_field_list,
)
from fides.api.task.conditional_dependencies.schemas import (
    ConditionalDependencyFieldInfo,
)
from fides.api.task.conditional_dependencies.util import (
    create_conditional_dependency_field_info,
)


def _build_nested_field_dict(
    fields: list[ConditionalDependencyFieldInfo],
) -> dict[str, Any]:
    """Converts a flat list of ConditionalDependencyFieldInfo objects into a nested dictionary."""
    result: dict[str, Any] = {}

    for field in fields:
        path_parts = field.field_path.split(".")
        result = deep_update(result, set_nested_value(path_parts, field))

    return result


def _get_privacy_center_config_dict(
    db: Session,
) -> Optional[dict[str, Any]]:
    """Gets privacy center config dict from database."""
    config_dict: Optional[dict[str, Any]] = None

    # 1. Try default property config
    default_prop = Property.get_by(db, field="is_default", value=True)
    if default_prop and getattr(default_prop, "privacy_center_config", None):
        config_dict = default_prop.privacy_center_config  # type: ignore[return-value]

    # 2. Try single-row global config
    if not config_dict:
        privacy_center_config_record = db.query(PrivacyCenterConfigModel).first()
        if privacy_center_config_record:
            # The config field stores the config dict directly
            config_dict = privacy_center_config_record.config  # type: ignore[return-value]

    return config_dict


def _get_custom_fields_from_privacy_center_config(
    db: Session,
) -> dict[str, set[str]]:
    """Extracts custom field names per policy from privacy center configs."""
    config_dict = _get_privacy_center_config_dict(db)
    if not config_dict:
        return {}

    policy_custom_fields: dict[str, set[str]] = {}

    try:
        config = PrivacyCenterConfigSchema.model_validate(config_dict)
        if not config.actions:
            return {}
        for action in config.actions:
            if (
                not isinstance(action, PrivacyRequestOption)
                or not action.policy_key
                or not action.custom_privacy_request_fields
            ):
                continue
            field_names = set(action.custom_privacy_request_fields.keys())
            if field_names:
                policy_custom_fields[action.policy_key] = field_names
    except Exception as exc:  # pylint: disable=broad-except
        # If we can't parse the config, just return empty dict
        # Log the exception for debugging but don't fail
        logger.debug(f"Could not parse privacy center config: {exc}")

    return policy_custom_fields


def _get_identity_fields_from_privacy_center_config(
    db: Session,
) -> set[str]:
    """Extracts all unique identity field names from privacy center configs."""
    config_dict = _get_privacy_center_config_dict(db)
    if not config_dict:
        return set()

    identity_field_names: set[str] = set()

    try:
        config = PrivacyCenterConfigSchema.model_validate(config_dict)
        if not config.actions:
            return set()
        for action in config.actions:
            if isinstance(action, PrivacyRequestOption) and action.identity_inputs:
                # Extract all keys from identity_inputs (both standard and custom)
                identity_inputs_dict = action.identity_inputs.model_dump(
                    exclude_none=True
                )
                identity_field_names.update(identity_inputs_dict.keys())
    except Exception as exc:  # pylint: disable=broad-except
        # If we can't parse the config, just return empty set
        # Log the exception for debugging but don't fail
        logger.debug(
            f"Could not parse privacy center config for identity fields: {exc}"
        )
    return identity_field_names


def set_nested_value(path: list[str], value: Any) -> dict[str, Any]:
    """
    Returns a dictionary with a nested value set at the path.

    Args:
        path: List of keys to traverse (e.g., ["policy", "key"])
        value: The value to set at the end of the path
    """
    result: dict[str, Any] = {}
    final_key = path[-1]
    current = result

    for key in path[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Set the final value
    current[final_key] = value
    return result


def build_privacy_request_fields() -> list[ConditionalDependencyFieldInfo]:
    """Builds a list of ConditionalDependencyFieldInfo objects for the PrivacyRequest model."""
    standard_field_names = {
        "created_at",
        "due_date",
        "identity_verified_at",
        "location",
        "origin",
        "requested_at",
        "source",
        "submitted_by",
    }
    return [
        create_conditional_dependency_field_info(
            f"privacy_request.{field_name}", "string", f"Privacy request {field_name}"
        )
        for field_name in standard_field_names
    ]


def build_policy_fields(db: Session) -> list[ConditionalDependencyFieldInfo]:
    """Builds a list of ConditionalDependencyFieldInfo objects for the Policy model."""
    standard_field_names = {
        "id",
        "name",
        "key",
        "description",
        "execution_timeframe",
        "rules",
        "drp_action",
    }
    fields = [
        create_conditional_dependency_field_info(
            f"privacy_request.policy.{field_name}",
            "string",
            f"Privacy request policy {field_name}",
        )
        for field_name in standard_field_names
    ]
    policy_custom_fields: dict[str, set[str]] = (
        _get_custom_fields_from_privacy_center_config(db)
    )
    # Collect all unique custom field names from all policies
    all_custom_field_names: set[str] = set()
    for field_names in policy_custom_fields.values():
        all_custom_field_names.update(field_names)

    for field_name in all_custom_field_names:
        policies_with_field = [
            policy_key
            for policy_key, field_names in policy_custom_fields.items()
            if field_name in field_names
        ]
        fields.append(
            create_conditional_dependency_field_info(
                f"privacy_request.policy.custom_privacy_request_fields.{field_name}",
                "string",
                f"Privacy request policy custom field {field_name} available for policies: {', '.join(sorted(policies_with_field))}",
            )
        )
    return fields


def build_identity_fields(db: Session) -> list[ConditionalDependencyFieldInfo]:
    """
    Build a list of ConditionalDependencyFieldInfo objects for the Identity model.
    """
    standard_field_names = {
        "email",
        "phone_number",
        "external_id",
        "fides_user_device_id",
        "ljt_readerID",
        "ga_client_id",
    }
    fields = [
        create_conditional_dependency_field_info(
            f"privacy_request.identity.{field_name}",
            "string",
            f"Privacy request identity {field_name}",
        )
        for field_name in standard_field_names
    ]
    config_identity_fields = _get_identity_fields_from_privacy_center_config(db)
    for config_field_name in config_identity_fields:
        # Skip standard fields that are already added
        if config_field_name not in standard_field_names:
            fields.append(
                create_conditional_dependency_field_info(
                    f"privacy_request.identity.custom_identity_fields.{config_field_name}",
                    "string",
                    f"Custom identity field '{config_field_name}'",
                )
            )
    return fields


def get_available_privacy_request_fields_list(
    db: Session,
) -> list[ConditionalDependencyFieldInfo]:
    """
    Generate a list of available fields for privacy request conditional dependencies.

    Args:
        db: Database session to query privacy center configs for custom fields

    Returns:
        List of ConditionalDependencyFieldInfo objects
        {
            ConditionalDependencyFieldInfo(...),
            ConditionalDependencyFieldInfo(...),
            ...
        }
    """
    # Add derived convenience fields
    fields = build_privacy_request_fields()
    fields.extend(build_policy_fields(db))
    fields.extend(build_identity_fields(db))
    fields.extend(build_convenience_field_list())
    return fields


def get_available_privacy_request_fields_dict(db: Session) -> dict[str, Any]:
    """Generate a nested dictionary of available fields for privacy request conditional dependencies.

    Args:
        db: Database session to query privacy center configs for custom fields

    Returns:
        Nested dictionary structure like:
        {
            "privacy_request": {
                "policy": {
                    "has_access_rule": ConditionalDependencyFieldInfo(...),
                    "custom_privacy_request_fields": {
                        "first_name": ConditionalDependencyFieldInfo(...),
                        "last_name": ConditionalDependencyFieldInfo(...),
                        ...
                    },
                    ...
                },
                "id": ConditionalDependencyFieldInfo(...),
                ...
            }
        }
    """
    return _build_nested_field_dict(get_available_privacy_request_fields_list(db))
