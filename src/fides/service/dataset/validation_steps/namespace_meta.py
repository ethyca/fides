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
        has_connection_defaults = all(
            field_name in context.connection_config.secrets
            and context.connection_config.secrets[field_name]
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
            try:
                namespace_meta_class(**namespace_meta)
            except Exception as e:
                raise ValidationError(
                    f"Invalid namespace metadata for {connection_type}: {str(e)}"
                )
