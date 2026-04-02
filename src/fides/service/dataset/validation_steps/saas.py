from typing import List, Optional

from fideslang.models import Dataset as FideslangDataset
from fideslang.models import DatasetField
from loguru import logger
from pydantic import ValidationError as PydanticValidationError

from fides.api.common_exceptions import SaaSConfigNotFoundException, ValidationError
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import to_graph_field
from fides.api.schemas.dataset import DatasetFieldWarning
from fides.api.schemas.saas.saas_config import SaaSConfig
from fides.service.connection.merge_configs_util import (
    get_saas_config_referenced_field_paths,
)
from fides.service.dataset.dataset_validator import (
    DatasetValidationContext,
    DatasetValidationStep,
)

from fides.api.models.sql_models import (  # type: ignore[attr-defined] # isort: skip
    Dataset as CtlDataset,
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


MUTABLE_DATASET_FIELDS = {"collections"}


def _restore_immutable_fields(
    dataset: FideslangDataset,
    existing_dataset: Optional[FideslangDataset] = None,
) -> List[DatasetFieldWarning]:
    """
    Restore top-level immutable fields to their original values.
    Every field outside ``collections`` is considered immutable.
    Returns structured warnings for each field that was restored.
    """
    if not existing_dataset:
        return []

    warnings: List[DatasetFieldWarning] = []
    for field_name in dataset.model_fields:
        if field_name in MUTABLE_DATASET_FIELDS:
            continue
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


def _resolve_field_path(
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
        resolved = _find_field_by_name(current_fields, part)
        if resolved is None:
            return None
        current_fields = resolved.fields or []
    return resolved


def _restore_nested_field(
    parent_fields: list[DatasetField],
    path_parts: list[str],
    existing_parent_fields: list[DatasetField],
) -> bool:
    """
    Restore a nested field described by *path_parts* into *parent_fields*,
    creating intermediate containers from *existing_parent_fields* as needed.

    Returns ``True`` if the field was successfully restored.
    """
    if not path_parts:
        return False

    name = path_parts[0]

    if len(path_parts) == 1:
        # Leaf – restore directly from existing
        existing_field = _find_field_by_name(existing_parent_fields, name)
        if existing_field:
            parent_fields.append(existing_field)
            return True
        return False

    # Intermediate – make sure the container exists in parent_fields
    container = _find_field_by_name(parent_fields, name)
    existing_container = _find_field_by_name(existing_parent_fields, name)
    if existing_container is None:
        return False

    if container is None:
        # Container itself was removed – re-create it from existing
        parent_fields.append(existing_container)
        return True  # whole subtree restored

    # Container exists – recurse
    if container.fields is None:
        container.fields = []
    return _restore_nested_field(
        container.fields,
        path_parts[1:],
        existing_container.fields or [],
    )


def _restore_protected_structure(
    connection_config: ConnectionConfig,
    dataset: FideslangDataset,
    existing_dataset: Optional[FideslangDataset] = None,
) -> List[DatasetFieldWarning]:
    """
    Restore protected structural elements (collections and protected fields)
    to their original values. User edits to non-protected parts are kept.
    Returns structured warnings for each restoration.

    Requires ``connection_config.saas_config`` to be non-None (the caller in
    ``SaaSValidationStep.validate`` guarantees this).
    """
    if not connection_config.saas_config:
        return []

    saas_config = SaaSConfig(**connection_config.saas_config)
    instance_key = connection_config.saas_config["fides_key"]
    warnings: List[DatasetFieldWarning] = []

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
        existing_by_name = {col.name: col for col in existing_dataset.collections}
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
            else:
                warnings.append(
                    DatasetFieldWarning(
                        collection=col_name,
                        message=f"Collection '{col_name}' is missing but could not "
                        f"be restored (not found in existing dataset).",
                    )
                )
                logger.warning(
                    "Collection '{}' missing from SaaS dataset '{}' "
                    "and not found in existing dataset for restoration",
                    col_name,
                    dataset.fides_key,
                )
    elif removed and not existing_dataset:
        for col_name in sorted(removed):
            warnings.append(
                DatasetFieldWarning(
                    collection=col_name,
                    message=f"Collection '{col_name}' is missing but could not "
                    f"be restored (no existing dataset found).",
                )
            )
            logger.warning(
                "Collection '{}' missing from SaaS dataset '{}' on first creation "
                "and could not be restored",
                col_name,
                dataset.fides_key,
            )

    # Restore protected fields: cannot delete fields referenced by SaaS config
    protected_fields = get_saas_config_referenced_field_paths(saas_config, instance_key)
    existing_collections_by_name = (
        {col.name: col for col in existing_dataset.collections}
        if existing_dataset
        else {}
    )

    for collection_name, field_path in protected_fields:
        # Find the collection in the incoming dataset
        collection = next(
            (col for col in dataset.collections if col.name == collection_name),
            None,
        )
        if not collection:
            continue

        if _resolve_field_path(collection.fields, field_path) is None:
            # Field was deleted — restore from existing dataset
            existing_collection = existing_collections_by_name.get(collection_name)
            if existing_collection:
                path_parts = field_path.split(".")
                restored = _restore_nested_field(
                    collection.fields,
                    path_parts,
                    existing_collection.fields,
                )
                if restored:
                    warnings.append(
                        DatasetFieldWarning(
                            collection=collection_name,
                            field=field_path,
                            message=f"Restored field '{field_path}' in collection "
                            f"'{collection_name}' (referenced by SaaS config).",
                        )
                    )
                    logger.info(
                        "Restored deleted protected field '{}.{}' on SaaS dataset '{}'",
                        collection_name,
                        field_path,
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

            # Fetch the existing dataset once and pass to both helpers
            existing_record = (
                context.db.query(CtlDataset)
                .filter(CtlDataset.fides_key == context.dataset.fides_key)
                .first()
            )
            existing_dataset: Optional[FideslangDataset] = None
            if existing_record:
                try:
                    existing_dataset = FideslangDataset.model_validate(existing_record)
                except PydanticValidationError:
                    logger.warning(
                        "Could not parse existing dataset '{}' — "
                        "proceeding without existing record for validation",
                        context.dataset.fides_key,
                    )

            # Restore immutable fields and protected structure instead of rejecting
            context.warnings.extend(
                _restore_immutable_fields(context.dataset, existing_dataset)
            )
            context.warnings.extend(
                _restore_protected_structure(
                    context.connection_config, context.dataset, existing_dataset
                )
            )
