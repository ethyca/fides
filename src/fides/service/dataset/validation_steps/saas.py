from copy import deepcopy
from dataclasses import dataclass
from typing import List, Optional

from fideslang.models import Dataset as FideslangDataset
from fideslang.models import DatasetField, FidesMeta
from loguru import logger
from pydantic import ValidationError as PydanticValidationError

from fides.api.common_exceptions import SaaSConfigNotFoundException, ValidationError
from fides.api.graph.utils import find_field_by_name, resolve_field_path
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.models.datasetconfig import to_graph_field
from fides.api.schemas.dataset import DatasetFieldWarning
from fides.service.connection.merge_configs_util import (
    get_saas_config_referenced_field_paths,
)
from fides.service.dataset.dataset_service import (
    DatasetNotFoundException,
    _get_ctl_dataset,
)
from fides.service.dataset.dataset_validator import (
    DatasetValidationContext,
    DatasetValidationStep,
)


def validate_saas_dataset(
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


# Everything outside this set is treated as immutable on SaaS datasets.
# If a new FideslangDataset field should be user-editable, add it here.
MUTABLE_DATASET_FIELDS = frozenset({"collections"})


def restore_immutable_fields(
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
            setattr(dataset, field_name, deepcopy(existing_value))
            warnings.append(
                DatasetFieldWarning(
                    field=field_name,
                    action="restored",
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


def restore_nested_field(
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
        existing_field = find_field_by_name(existing_parent_fields, name)
        if existing_field:
            parent_fields.append(deepcopy(existing_field))
            return True
        return False

    # Intermediate – make sure the container exists in parent_fields
    container = find_field_by_name(parent_fields, name)
    existing_container = find_field_by_name(existing_parent_fields, name)
    if existing_container is None:
        return False

    if container is None:
        # Container itself was removed – re-create it from existing
        parent_fields.append(deepcopy(existing_container))
        return True  # whole subtree restored

    # Container exists – recurse
    if container.fields is None:
        container.fields = []
    return restore_nested_field(
        container.fields,
        path_parts[1:],
        existing_container.fields or [],
    )


def _emit_failed_collection_warning(
    warnings: List[DatasetFieldWarning],
    col_name: str,
    dataset_fides_key: str,
    reason: str,
) -> None:
    """Emit a structured warning when a collection could not be restored."""
    warnings.append(
        DatasetFieldWarning(
            collection=col_name,
            action="failed",
            message=f"Collection '{col_name}' is missing but could not "
            f"be restored ({reason}).",
        )
    )
    logger.warning(
        "Collection '{}' missing from SaaS dataset '{}' and could not be restored: {}",
        col_name,
        dataset_fides_key,
        reason,
    )


def restore_protected_structure(
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

    saas_config = connection_config.get_saas_config()
    assert saas_config is not None  # guaranteed by the guard above
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
                    action="removed",
                    message=f"Removed collection '{col_name}' "
                    f"(cannot add collections to a SaaS dataset).",
                )
            )
            logger.warning(
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
                dataset.collections.append(deepcopy(existing_by_name[col_name]))
                warnings.append(
                    DatasetFieldWarning(
                        collection=col_name,
                        action="restored",
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
                _emit_failed_collection_warning(
                    warnings,
                    col_name,
                    dataset.fides_key,
                    "not found in existing dataset",
                )
    elif removed and not existing_dataset:
        for col_name in sorted(removed):
            _emit_failed_collection_warning(
                warnings,
                col_name,
                dataset.fides_key,
                "no existing dataset found",
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

        if resolve_field_path(collection.fields, field_path) is None:
            # Field was deleted — restore from existing dataset
            existing_collection = existing_collections_by_name.get(collection_name)
            if existing_collection:
                path_parts = field_path.split(".")
                restored = restore_nested_field(
                    collection.fields,
                    path_parts,
                    existing_collection.fields,
                )
                if restored:
                    warnings.append(
                        DatasetFieldWarning(
                            collection=collection_name,
                            field=field_path,
                            action="restored",
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
                else:
                    warnings.append(
                        DatasetFieldWarning(
                            collection=collection_name,
                            field=field_path,
                            action="failed",
                            message=f"Could not restore field '{field_path}' in collection "
                            f"'{collection_name}' (not found in existing dataset).",
                        )
                    )
                    logger.warning(
                        "Could not restore protected field '{}.{}' on SaaS dataset '{}'",
                        collection_name,
                        field_path,
                        dataset.fides_key,
                    )

    return warnings


def restore_field_meta_attributes(
    dataset: FideslangDataset,
    existing_dataset: Optional[FideslangDataset] = None,
) -> List[DatasetFieldWarning]:
    """
    Protect immutable fides_meta attributes on SaaS dataset fields.

    - **primary_key**: field cannot be deleted; value cannot be changed
    - **identity**: value cannot be changed
    - **references**: value cannot be changed

    Only the specific attribute is restored — other metadata edits persist.
    Returns structured warnings for each restoration.
    """
    if not existing_dataset:
        return []

    warnings: List[DatasetFieldWarning] = []
    existing_by_name = {col.name: col for col in existing_dataset.collections}

    for collection in dataset.collections:
        existing_collection = existing_by_name.get(collection.name)
        if not existing_collection:
            continue

        _restore_protected_meta(
            collection.fields,
            existing_collection.fields,
            collection.name,
            dataset.fides_key,
            warnings,
        )

    return warnings


@dataclass(frozen=True)
class _ProtectedAttr:
    """Configuration for a single protected fides_meta attribute."""

    attr: str
    label: str
    compare_as_bool: bool = False
    prevents_deletion: bool = False


# To protect a new fides_meta attribute, add an entry here.
PROTECTED_META_ATTRS: list[_ProtectedAttr] = [
    _ProtectedAttr(
        attr="primary_key",
        label="primary key",
        compare_as_bool=True,
        prevents_deletion=True,
    ),
    _ProtectedAttr(attr="identity", label="identity"),
    _ProtectedAttr(attr="references", label="references"),
]


def _restore_protected_meta(
    incoming_fields: list[DatasetField],
    existing_fields: list[DatasetField],
    collection_name: str,
    dataset_fides_key: str,
    warnings: List[DatasetFieldWarning],
    prefix: str = "",
) -> None:
    """Restore protected fides_meta attributes to their existing values.

    Walks both trees in parallel. Attributes marked with
    ``prevents_deletion=True`` also prevent the field itself from being deleted.
    """
    # Deletion protection for fields with prevents_deletion attrs set to truthy
    deletion_attrs = [p for p in PROTECTED_META_ATTRS if p.prevents_deletion]
    for existing_field in existing_fields:
        if find_field_by_name(incoming_fields, existing_field.name) is not None:
            continue
        if not existing_field.fides_meta:
            continue

        protecting_attr = next(
            (
                p
                for p in deletion_attrs
                if getattr(existing_field.fides_meta, p.attr, None)
            ),
            None,
        )
        if not protecting_attr:
            continue

        path = f"{prefix}{existing_field.name}" if prefix else existing_field.name
        restored = restore_nested_field(
            incoming_fields,
            [existing_field.name],
            existing_fields,
        )
        action = "restored" if restored else "failed"
        message = (
            f"Restored {protecting_attr.label} field '{path}' in "
            f"collection '{collection_name}' "
            f"(cannot delete {protecting_attr.label} fields)."
            if restored
            else f"Could not restore {protecting_attr.label} field '{path}' "
            f"in collection '{collection_name}'."
        )
        warnings.append(
            DatasetFieldWarning(
                collection=collection_name,
                field=path,
                action=action,
                message=message,
            )
        )
        (logger.info if restored else logger.warning)(
            "{} {} field '{}.{}' on SaaS dataset '{}'",
            "Restored deleted" if restored else "Could not restore",
            protecting_attr.label,
            collection_name,
            path,
            dataset_fides_key,
        )

    # Attribute protection: compare each protected attr on fields in both trees
    for field in incoming_fields:
        path = f"{prefix}{field.name}" if prefix else field.name
        matching_existing = find_field_by_name(existing_fields, field.name)
        if matching_existing is None:
            if field.fields:
                _restore_protected_meta(
                    field.fields,
                    [],
                    collection_name,
                    dataset_fides_key,
                    warnings,
                    f"{path}.",
                )
            continue

        existing_meta = matching_existing.fides_meta
        incoming_meta = field.fides_meta

        for protected in PROTECTED_META_ATTRS:
            existing_val = (
                getattr(existing_meta, protected.attr, None) if existing_meta else None
            )
            incoming_val = (
                getattr(incoming_meta, protected.attr, None) if incoming_meta else None
            )

            if protected.compare_as_bool:
                changed = bool(existing_val) != bool(incoming_val)
            else:
                changed = existing_val != incoming_val

            if changed:
                restored_val = deepcopy(existing_val)
                if not incoming_meta:
                    field.fides_meta = FidesMeta(**{protected.attr: restored_val})
                    incoming_meta = field.fides_meta
                else:
                    setattr(incoming_meta, protected.attr, restored_val)
                warnings.append(
                    DatasetFieldWarning(
                        collection=collection_name,
                        field=path,
                        action="restored",
                        message=f"Restored {protected.label} on field '{path}' "
                        f"in collection '{collection_name}' "
                        f"({protected.label} cannot be changed).",
                    )
                )
                logger.info(
                    "Restored {} on '{}.{}' in SaaS dataset '{}'",
                    protected.label,
                    collection_name,
                    path,
                    dataset_fides_key,
                )

        # Recurse into nested fields
        if field.fields:
            _restore_protected_meta(
                field.fields,
                matching_existing.fields or [],
                collection_name,
                dataset_fides_key,
                warnings,
                f"{path}.",
            )


class SaaSValidationStep(DatasetValidationStep):
    """Validates SaaS-specific requirements"""

    def validate(self, context: DatasetValidationContext) -> None:
        if (
            context.connection_config
            and context.connection_config.connection_type == ConnectionType.saas
        ):
            validate_saas_dataset(context.connection_config, context.dataset)

            # Fetch the existing dataset once and pass to both helpers
            try:
                existing_record = _get_ctl_dataset(
                    context.db, context.dataset.fides_key
                )
            except DatasetNotFoundException:
                existing_record = None
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

            # Restore immutable fields, protected structure, and protected
            # field metadata (primary keys, identity, references)
            context.warnings.extend(
                restore_immutable_fields(context.dataset, existing_dataset)
            )
            context.warnings.extend(
                restore_protected_structure(
                    context.connection_config, context.dataset, existing_dataset
                )
            )
            context.warnings.extend(
                restore_field_meta_attributes(context.dataset, existing_dataset)
            )
