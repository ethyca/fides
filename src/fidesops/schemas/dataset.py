from typing import Dict, List, Optional

from fideslang.models import Dataset, DatasetCollection, DatasetField
from pydantic import BaseModel, root_validator, validator, ConstrainedStr

from fidesops.common_exceptions import InvalidDataTypeValidationError
from fidesops.common_exceptions import InvalidDataLengthValidationError
from fidesops.graph.config import EdgeDirection
from fidesops.graph.data_type import DataType
from fidesops.models.policy import _validate_data_category
from fidesops.schemas.api import BulkResponse, BulkUpdateFailed
from fidesops.schemas.base_class import BaseSchema
from fidesops.schemas.shared_schemas import FidesOpsKey


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

    if data_type_str is not None:
        try:
            DataType[data_type_str]  # pylint: disable=pointless-statement
            return data_type_str
        except KeyError:
            raise InvalidDataTypeValidationError(
                f"The data type {data_type_str} is not supported."
            )

    return None


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

    @validator("data_type")
    def valid_data_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate that all annotated data categories exist in the taxonomy"""
        return _valid_data_type(v)

    @validator("length")
    def valid_length(cls, v: Optional[int]) -> Optional[int]:
        """Validate that the provided length is valid"""
        return _valid_data_length(v)


class FidesopsDatasetField(DatasetField):
    """Extends fideslang DatasetField model with additional Fidesops annotations"""

    fidesops_meta: Optional[FidesopsMeta]

    @root_validator(pre=True)
    def prevent_nested_collections(cls, values: Dict) -> Dict:
        """
        Defensively check to ensure that there are no nested collections.

        NOTE: This should be removed once nesting support is implemented!
        """
        assert "fields" not in values, f"unsupported nested collection: {values}"
        return values

    @validator("data_categories")
    def valid_data_categories(
        cls, v: Optional[List[FidesOpsKey]]
    ) -> Optional[List[FidesOpsKey]]:
        """Validate that all annotated data categories exist in the taxonomy"""
        return _valid_data_categories(v)


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
    query: Optional[str]
