from typing import Optional, Set

from fideslang.models import Dataset as FideslangDataset
from fideslang.models import DatasetField
from sqlalchemy.orm import Session

from fides.api.common_exceptions import SaaSConfigNotFoundException, ValidationError
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import to_graph_field
from fides.api.schemas.saas.saas_config import SaaSConfig
from fides.service.connection.merge_configs_util import (
    get_saas_config_referenced_fields,
)
from fides.service.dataset.dataset_validator import (
    DatasetValidationContext,
    DatasetValidationStep,
)

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
)


def _get_field_names(fields: list[DatasetField]) -> Set[str]:
    """Get field names from a list of dataset fields."""
    return {field.name for field in fields}


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


_IMMUTABLE_DATASET_FIELDS = (
    "fides_key",
    "organization_fides_key",
    "name",
    "description",
)


def _validate_saas_dataset_immutable_fields(
    db: Session, dataset: FideslangDataset
) -> None:
    """
    Validate that top-level dataset metadata fields have not been changed.
    These fields come from the connector template and should not be user-editable.
    """
    existing = (
        db.query(CtlDataset).filter(CtlDataset.fides_key == dataset.fides_key).first()
    )
    if not existing:
        return

    existing_dataset = FideslangDataset.model_validate(existing)
    for field_name in _IMMUTABLE_DATASET_FIELDS:
        existing_value = getattr(existing_dataset, field_name)
        incoming_value = getattr(dataset, field_name)
        if existing_value != incoming_value:
            raise ValidationError(f"Cannot modify '{field_name}' on a SaaS dataset.")


def _validate_saas_dataset_structure(
    db: Session, connection_config: ConnectionConfig, dataset: FideslangDataset
) -> None:
    """
    Validate that the dataset does not modify immutable fields,
    add/remove collections, or delete fields referenced by the SaaS config.
    """
    _validate_saas_dataset_immutable_fields(db, dataset)

    saas_config = SaaSConfig(**connection_config.saas_config)
    instance_key = connection_config.saas_config["fides_key"]

    # Validate collections: cannot add or remove
    expected_collections = {endpoint.name for endpoint in saas_config.endpoints}
    actual_collections = {col.name for col in dataset.collections}

    added = actual_collections - expected_collections
    if added:
        raise ValidationError(
            f"Cannot add collections to a SaaS dataset. "
            f"Unexpected collections: {', '.join(sorted(added))}"
        )

    removed = expected_collections - actual_collections
    if removed:
        raise ValidationError(
            f"Cannot remove collections from a SaaS dataset. "
            f"Missing collections: {', '.join(sorted(removed))}"
        )

    # Validate protected fields: cannot delete fields referenced by SaaS config
    protected_fields = get_saas_config_referenced_fields(saas_config, instance_key)
    dataset_fields_by_collection = {
        col.name: _get_field_names(col.fields) for col in dataset.collections
    }

    for collection_name, field_name in protected_fields:
        collection_fields = dataset_fields_by_collection.get(collection_name, set())
        if field_name not in collection_fields:
            raise ValidationError(
                f"Cannot delete field '{field_name}' from collection "
                f"'{collection_name}' because it is referenced by the SaaS config."
            )


class SaaSValidationStep(DatasetValidationStep):
    """Validates SaaS-specific requirements"""

    def validate(self, context: DatasetValidationContext) -> None:
        if (
            context.connection_config
            and context.connection_config.connection_type == ConnectionType.saas
        ):
            _validate_saas_dataset(context.connection_config, context.dataset)
            _validate_saas_dataset_structure(
                context.db, context.connection_config, context.dataset
            )
