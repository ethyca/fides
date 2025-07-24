from fideslang.models import DatasetField

from fides.api.common_exceptions import ValidationError
from fides.api.service.masking.strategy.masking_strategy import MaskingStrategy
from fides.service.dataset.dataset_validator import (
    DatasetValidationContext,
    DatasetValidationStep,
)


class MaskingStrategyValidationStep(DatasetValidationStep):
    """Validates masking strategy overrides"""

    def validate(self, context: DatasetValidationContext) -> None:
        """
        Validates that field-level masking overrides do not require secret keys.
        When handling a privacy request, we use the `cache_data` function to review the policies and identify which masking strategies need secret keys generated and cached.
        Currently, we are avoiding the additional complexity of scanning datasets for masking overrides.
        """

        def validate_field(dataset_field: DatasetField) -> None:
            if dataset_field.fields:
                for subfield in dataset_field.fields:
                    validate_field(subfield)
            else:
                if (
                    dataset_field.fides_meta
                    and dataset_field.fides_meta.masking_strategy_override
                ):
                    strategy: MaskingStrategy = MaskingStrategy.get_strategy(
                        dataset_field.fides_meta.masking_strategy_override.strategy,
                        dataset_field.fides_meta.masking_strategy_override.configuration,  # type: ignore[arg-type]
                    )
                    if strategy.secrets_required():
                        raise ValidationError(
                            f"Masking strategy '{strategy.name}' with required secrets not allowed as an override."
                        )

        for collection in context.dataset.collections:
            for field in collection.fields:
                validate_field(field)
