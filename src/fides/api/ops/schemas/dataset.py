from typing import Any, Dict, List, Optional

from fideslang.models import Dataset, DatasetCollection, DatasetFieldBase
from pydantic import BaseModel, ConstrainedStr, Field, validator

from fides.api.ops.common_exceptions import (
    InvalidDataLengthValidationError,
    InvalidDataTypeValidationError,
)
from fides.api.ops.graph.config import EdgeDirection
from fides.api.ops.graph.data_type import is_valid_data_type, parse_data_type_string
from fides.api.ops.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.ops.schemas.base_class import BaseSchema
from fides.api.ops.schemas.shared_schemas import FidesOpsKey
from fides.api.ops.util.data_category import _validate_data_category


def _valid_data_categories(
    data_categories: Optional[List[FidesOpsKey]],
) -> Optional[List[FidesOpsKey]]:
    """
    Ensure that every data category provided matches a valid category defined in
    the current taxonomy. Throws an error if any of the categories are invalid,
    or otherwise returns the list of categories unchanged.
    """

    if data_categories:
        return [dc for dc in data_categories if _validate_data_category(dc)]
    return data_categories


def _valid_data_type(data_type_str: Optional[str]) -> Optional[str]:
    """If the data_type is provided ensure that it is a member of DataType."""

    dt, _ = parse_data_type_string(data_type_str)
    if not is_valid_data_type(dt):  # type: ignore
        raise InvalidDataTypeValidationError(
            f"The data type {data_type_str} is not supported."
        )

    return data_type_str


def _valid_data_length(data_length: Optional[int]) -> Optional[int]:
    """If the data_length is provided ensure that it is a positive non-zero value."""

    if data_length is not None and data_length <= 0:
        raise InvalidDataLengthValidationError(
            f"Illegal length ({data_length}). Only positive non-zero values are allowed."
        )

    return data_length


class FidesCollectionKey(ConstrainedStr):
    """
    Dataset:Collection name where both dataset and collection names are valid FidesKeys
    """

    @classmethod
    def validate(cls, value: str) -> str:
        """
        Overrides validation to check FidesCollectionKey format, and that both the dataset
        and collection names have the FidesKey format.
        """
        values = value.split(".")
        if len(values) == 2:
            FidesOpsKey.validate(values[0])
            FidesOpsKey.validate(values[1])
            return value
        raise ValueError(
            "FidesCollection must be specified in the form 'FidesKey.FidesKey'"
        )


# NOTE: this extends pydantic.BaseModel instead of our BaseSchema, for
# consistency with other fideslang models
class FidesopsDatasetReference(BaseModel):
    """Reference to a field from another Collection"""

    dataset: FidesOpsKey
    field: str
    direction: Optional[EdgeDirection]


class FidesopsDatasetMeta(BaseModel):
    """ "Dataset-level fidesops-specific annotations used for query traversal"""

    after: Optional[List[FidesOpsKey]]


class FidesopsCollectionMeta(BaseModel):
    """Collection-level fidesops-specific annotations used for query traversal"""

    after: Optional[List[FidesCollectionKey]]


class FidesopsMeta(BaseModel):
    """Fidesops-specific annotations used for query traversal"""

    references: Optional[List[FidesopsDatasetReference]]
    identity: Optional[str]
    primary_key: Optional[bool]
    data_type: Optional[str]
    """Optionally specify the data type. Fidesops will attempt to cast values to this type when querying."""
    length: Optional[int]
    """Optionally specify the allowable field length. Fidesops will not generate values that exceed this size."""
    return_all_elements: Optional[bool]
    """Optionally specify to query for the entire array if the array is an entrypoint into the node. Default is False."""
    read_only: Optional[bool]
    """Optionally specify if a field is read-only, meaning it can't be updated or deleted."""

    @validator("data_type")
    def valid_data_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate that all annotated data categories exist in the taxonomy"""
        return _valid_data_type(v)

    @validator("length")
    def valid_length(cls, v: Optional[int]) -> Optional[int]:
        """Validate that the provided length is valid"""
        return _valid_data_length(v)


class FidesopsDatasetField(DatasetFieldBase):
    """Extends fideslang DatasetField model with additional Fidesops annotations"""

    fidesops_meta: Optional[FidesopsMeta]
    fields: Optional[List["FidesopsDatasetField"]] = []

    @validator("data_categories")
    def valid_data_categories(
        cls, v: Optional[List[FidesOpsKey]]
    ) -> Optional[List[FidesOpsKey]]:
        """Validate that all annotated data categories exist in the taxonomy"""
        return _valid_data_categories(v)

    @validator("fidesops_meta")
    def valid_meta(cls, meta_values: Optional[FidesopsMeta]) -> Optional[FidesopsMeta]:
        """Validate upfront that the return_all_elements flag can only be specified on array fields"""
        if not meta_values:
            return meta_values

        is_array: bool = bool(
            meta_values.data_type and meta_values.data_type.endswith("[]")
        )
        if not is_array and meta_values.return_all_elements is not None:
            raise ValueError(
                "The 'return_all_elements' attribute can only be specified on array fields."
            )
        return meta_values

    @validator("fields")
    def validate_object_fields(
        cls,
        fields: Optional[List["FidesopsDatasetField"]],
        values: Dict[str, Any],
    ) -> Optional[List["FidesopsDatasetField"]]:
        """Two validation checks for object fields:
        - If there are sub-fields specified, type should be either empty or 'object'
        - Additionally object fields cannot have data_categories.
        """
        declared_data_type = None

        if values.get("fidesops_meta"):
            declared_data_type = values["fidesops_meta"].data_type

        if fields and declared_data_type:
            data_type, _ = parse_data_type_string(declared_data_type)
            if data_type != "object":
                raise InvalidDataTypeValidationError(
                    f"The data type {data_type} is not compatible with specified sub-fields."
                )

        if (fields or declared_data_type == "object") and values.get("data_categories"):
            raise ValueError(
                "Object fields cannot have specified data_categories. Specify category on sub-field instead"
            )

        return fields


# this is required for the recursive reference in the pydantic model:
FidesopsDatasetField.update_forward_refs()


class FidesopsDatasetCollection(DatasetCollection):
    """Overrides fideslang DatasetCollection model with additional Fidesops annotations"""

    fidesops_meta: Optional[FidesopsCollectionMeta]
    fields: List[FidesopsDatasetField]
    """Overrides fideslang.models.DatasetCollection.fields"""

    @validator("data_categories")
    def valid_data_categories(
        cls, v: Optional[List[FidesOpsKey]]
    ) -> Optional[List[FidesOpsKey]]:
        """Validate that all annotated data categories exist in the taxonomy"""
        return _valid_data_categories(v)


class FidesopsDataset(Dataset):
    """Overrides fideslang Collection model with additional Fidesops annotations"""

    fides_key: FidesOpsKey = Field(
        description="A unique key used to identify this resource."
    )
    fidesops_meta: Optional[FidesopsDatasetMeta]
    collections: List[FidesopsDatasetCollection]
    """Overrides fideslang.models.Collection.collections"""

    @validator("data_categories")
    def valid_data_categories(
        cls, v: Optional[List[FidesOpsKey]]
    ) -> Optional[List[FidesOpsKey]]:
        """Validate that all annotated data categories exist in the taxonomy"""
        return _valid_data_categories(v)


class DatasetTraversalDetails(BaseSchema):
    """
    Describes whether or not the parent dataset is traversable; if not, includes
    an error message describing the traversal issues.
    """

    is_traversable: bool
    msg: Optional[str]


class ValidateDatasetResponse(BaseSchema):
    """
    Response model for validating a dataset, which includes both the dataset
    itself (if valid) plus a details object describing if the dataset is
    traversable or not.
    """

    dataset: FidesopsDataset
    traversal_details: DatasetTraversalDetails


class BulkPutDataset(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of Datasets."""

    succeeded: List[FidesopsDataset]
    failed: List[BulkUpdateFailed]


class CollectionAddressResponse(BaseSchema):
    """Schema for the representation of a collection in the graph"""

    dataset: Optional[str]
    collection: Optional[str]


class DryRunDatasetResponse(BaseSchema):
    """
    Response model for dataset dry run
    """

    collectionAddress: CollectionAddressResponse
    query: Any
