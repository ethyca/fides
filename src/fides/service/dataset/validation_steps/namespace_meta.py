from pydantic import ValidationError as PydanticValidationError

import fides.api.schemas.namespace_meta  # noqa: F401  — triggers __init_subclass__ registration
from fides.api.common_exceptions import ValidationError
from fides.api.schemas.namespace_meta.namespace_meta import NamespaceMeta
from fides.service.dataset.dataset_validator import (
    DatasetValidationContext,
    DatasetValidationStep,
)


class NamespaceMetaValidationStep(DatasetValidationStep):
    """Validates that datasets have required namespace metadata based on connection type"""

    def validate(self, context: DatasetValidationContext) -> None:
        if not context.connection_config:
            return

        connection_type: str = context.connection_config.connection_type.value  # type: ignore[attr-defined]
        namespace_meta_class = NamespaceMeta.get_implementation(connection_type)
        if not namespace_meta_class:
            return

        # Check if dataset has namespace metadata
        namespace_meta = (
            context.dataset.fides_meta.namespace if context.dataset.fides_meta else None
        )

        # Get required secret fields from the namespace meta class
        required_fields = namespace_meta_class.get_fallback_secret_fields()
        secrets = context.connection_config.secrets or {}
        has_connection_defaults = all(
            field_name in secrets and secrets[field_name]
            for field_name, _ in required_fields
        )

        if not namespace_meta and not has_connection_defaults:
            field_descriptions = ", ".join(
                field_label for _, field_label in required_fields
            )
            raise ValidationError(
                f"Dataset for {connection_type} connection must either have namespace metadata "
                f"or the connection must have values for the following fields: {field_descriptions}"
            )
        if namespace_meta:
            # Skip validation when the namespace_meta connection_type doesn't
            # match this connection. This happens when datasets of mixed types
            # (e.g. BigQuery, Snowflake) are linked to a single connection.
            meta_connection_type = namespace_meta.get("connection_type")
            if meta_connection_type and meta_connection_type != connection_type:
                return

            # For legacy namespace_meta without connection_type, check whether
            # the provided fields overlap with the expected schema.  If there
            # is zero overlap the namespace belongs to a different connection
            # type and we skip.  If there IS overlap we backfill connection_type
            # and validate strictly so malformed namespaces are still caught.
            if not meta_connection_type:
                expected_fields = set(namespace_meta_class.model_fields.keys()) - {
                    "connection_type"
                }
                provided_fields = set(namespace_meta.keys()) - {"connection_type"}
                if not provided_fields & expected_fields:
                    return
                # Fields overlap — backfill connection_type so it's persisted
                namespace_meta["connection_type"] = connection_type

            try:
                namespace_meta_class(**namespace_meta)
            except PydanticValidationError as e:
                raise ValidationError(
                    f"Invalid namespace metadata for {connection_type}: {str(e)}"
                )
