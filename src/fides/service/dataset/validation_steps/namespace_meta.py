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

        # Check if connection config has required secret fields
        required_fields = NamespaceMeta.get_required_secret_fields(connection_type)
        has_connection_defaults = all(
            field in context.connection_config.secrets for field in required_fields
        )

        if not namespace_meta and not has_connection_defaults:
            required_fields_str = ", ".join(sorted(required_fields))
            raise ValidationError(
                f"Dataset for {connection_type} connection must either have namespace "
                f"metadata or the connection must have the following configuration: {required_fields_str}"
            )

        # If namespace metadata exists, validate it against the correct schema
        if namespace_meta:
            try:
                namespace_meta_class.model_validate(namespace_meta)
            except Exception as e:
                raise ValidationError(
                    f"Invalid namespace metadata for {connection_type}: {str(e)}"
                )
