from typing import List, Optional, Set

from fideslang.models import Dataset as FideslangDataset
from fideslang.models import DatasetField
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import SaaSConfigNotFoundException, ValidationError
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import to_graph_field
from fides.api.schemas.dataset import DatasetFieldWarning
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


def _restore_immutable_fields(
    db: Session, dataset: FideslangDataset
) -> List[DatasetFieldWarning]:
    """
    Restore top-level immutable fields to their original values.
    Returns structured warnings for each field that was restored.
    """
    existing = (
        db.query(CtlDataset).filter(CtlDataset.fides_key == dataset.fides_key).first()
    )
    if not existing:
        return []

    warnings: List[DatasetFieldWarning] = []
    existing_dataset = FideslangDataset.model_validate(existing)
    for field_name in _IMMUTABLE_DATASET_FIELDS:
        existing_value = getattr(existing_dataset, field_name)
        incoming_value = getattr(dataset, field_name)
        if existing_value != incoming_value:
            setattr(dataset, field_name, existing_value)
            warnings.append(
                DatasetFieldWarning(
                    field=field_name,
                    message=f"Restored '{field_name}' to its original value "
                    f"(cannot be modified on a SaaS dataset).",
                )
            )
            logger.info(
                "Restored immutable field '{}' on SaaS dataset '{}'",
                field_name,
                dataset.fides_key,
            )
    return warnings


def _find_field_by_name(
    fields: list[DatasetField], name: str
) -> Optional[DatasetField]:
    """Find a field by name in a list of dataset fields."""
    for field in fields:
        if field.name == name:
            return field
    return None


def _restore_protected_structure(
    db: Session, connection_config: ConnectionConfig, dataset: FideslangDataset
) -> List[DatasetFieldWarning]:
    """
    Restore protected structural elements (collections and protected fields)
    to their original values. User edits to non-protected parts are kept.
    Returns structured warnings for each restoration.
    """
    saas_config = SaaSConfig(**connection_config.saas_config)
    instance_key = connection_config.saas_config["fides_key"]
    warnings: List[DatasetFieldWarning] = []

    # Load existing dataset for restoring removed items
    existing_record = (
        db.query(CtlDataset)
        .filter(CtlDataset.fides_key == dataset.fides_key)
        .first()
    )
    existing_dataset = (
        FideslangDataset.model_validate(existing_record)
        if existing_record
        else None
    )

    # Restore collections: cannot add or remove
    expected_collections = {endpoint.name for endpoint in saas_config.endpoints}
    actual_collections = {col.name for col in dataset.collections}

    # Remove added collections (not in template)
    added = actual_collections - expected_collections
    if added:
        dataset.collections = [
            col for col in dataset.collections if col.name not in added
        ]
        for col_name in sorted(added):
            warnings.append(
                DatasetFieldWarning(
                    collection=col_name,
                    message=f"Removed collection '{col_name}' "
                    f"(cannot add collections to a SaaS dataset).",
                )
            )
            logger.info(
                "Removed user-added collection '{}' from SaaS dataset '{}'",
                col_name,
                dataset.fides_key,
            )

    # Restore removed collections from the existing dataset
    removed = expected_collections - {col.name for col in dataset.collections}
    if removed and existing_dataset:
        existing_by_name = {
            col.name: col for col in existing_dataset.collections
        }
        for col_name in sorted(removed):
            if col_name in existing_by_name:
                dataset.collections.append(existing_by_name[col_name])
                warnings.append(
                    DatasetFieldWarning(
                        collection=col_name,
                        message=f"Restored collection '{col_name}' "
                        f"(cannot remove collections from a SaaS dataset).",
                    )
                )
                logger.info(
                    "Restored removed collection '{}' on SaaS dataset '{}'",
                    col_name,
                    dataset.fides_key,
                )

    # Restore protected fields: cannot delete fields referenced by SaaS config
    protected_fields = get_saas_config_referenced_fields(saas_config, instance_key)
    existing_collections_by_name = (
        {col.name: col for col in existing_dataset.collections}
        if existing_dataset
        else {}
    )

    for collection_name, field_name in protected_fields:
        # Find the collection in the incoming dataset
        collection = next(
            (col for col in dataset.collections if col.name == collection_name),
            None,
        )
        if not collection:
            continue

        collection_fields = _get_field_names(collection.fields)
        if field_name not in collection_fields:
            # Field was deleted — restore from existing dataset
            existing_collection = existing_collections_by_name.get(collection_name)
            if existing_collection:
                existing_field = _find_field_by_name(
                    existing_collection.fields, field_name
                )
                if existing_field:
                    collection.fields.append(existing_field)
                    warnings.append(
                        DatasetFieldWarning(
                            collection=collection_name,
                            field=field_name,
                            message=f"Restored field '{field_name}' in collection "
                            f"'{collection_name}' (referenced by SaaS config).",
                        )
                    )
                    logger.info(
                        "Restored deleted protected field '{}.{}' on SaaS dataset '{}'",
                        collection_name,
                        field_name,
                        dataset.fides_key,
                    )

    return warnings


class SaaSValidationStep(DatasetValidationStep):
    """Validates SaaS-specific requirements"""

    def validate(self, context: DatasetValidationContext) -> None:
        if (
            context.connection_config
            and context.connection_config.connection_type == ConnectionType.saas
        ):
            _validate_saas_dataset(context.connection_config, context.dataset)

            # Restore immutable fields and protected structure instead of rejecting
            context.warnings.extend(
                _restore_immutable_fields(context.db, context.dataset)
            )
            context.warnings.extend(
                _restore_protected_structure(
                    context.db, context.connection_config, context.dataset
                )
            )
