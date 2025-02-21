from fideslang.models import Dataset as FideslangDataset

from fides.api.common_exceptions import SaaSConfigNotFoundException, ValidationError
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import to_graph_field
from fides.service.dataset.dataset_validator import (
    DatasetValidationContext,
    DatasetValidationStep,
)


def _validate_saas_dataset(
    connection_config: ConnectionConfig, dataset: FideslangDataset
) -> None:
    if connection_config.saas_config is None:
        raise SaaSConfigNotFoundException(
            f"Connection config '{connection_config.key}' must have a "
            "SaaS config before validating or adding a dataset"
        )

    fides_key = connection_config.saas_config["fides_key"]
    if fides_key != dataset.fides_key:
        raise ValidationError(
            f"The fides_key '{dataset.fides_key}' of the dataset "
            f"does not match the fides_key '{fides_key}' "
            "of the connection config"
        )
    for collection in dataset.collections:
        for field in collection.fields:
            graph_field = to_graph_field(field)
            if graph_field.references or graph_field.identity:
                raise ValidationError(
                    "A dataset for a ConnectionConfig type of 'saas' is not "
                    "allowed to have references or identities. Please add "
                    "them to the SaaS config."
                )


class SaaSValidationStep(DatasetValidationStep):
    """Validates SaaS-specific requirements"""

    def validate(self, context: DatasetValidationContext) -> None:
        if (
            context.connection_config
            and context.connection_config.connection_type == ConnectionType.saas
        ):
            _validate_saas_dataset(context.connection_config, context.dataset)
