from typing import Any, Dict, List, Optional, Union

from fideslang.models import Dataset, DatasetCollection
from fideslang.validation import FidesKey
from pydantic import ConfigDict, Field

from fides.api.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.schemas.base_class import FidesSchema


class DatasetTraversalDetails(FidesSchema):
    """
    Describes whether or not the parent dataset is traversable; if not, includes
    an error message describing the traversal issues.
    """

    is_traversable: bool
    msg: Optional[str]


class ValidateDatasetResponse(FidesSchema):
    """
    Response model for validating a dataset, which includes both the dataset
    itself (if valid) plus a details object describing if the dataset is
    traversable or not.
    """

    dataset: Dataset
    traversal_details: Optional[DatasetTraversalDetails]


class DatasetConfigCtlDataset(FidesSchema):
    fides_key: FidesKey  # The fides_key for the DatasetConfig
    ctl_dataset_fides_key: FidesKey  # The fides_key for the ctl_datasets record


class DatasetConfigSchema(FidesSchema):
    """Returns the DatasetConfig fides key and the linked Ctl Dataset"""

    fides_key: FidesKey
    ctl_dataset: Dataset
    model_config = ConfigDict(from_attributes=True)


class BulkPutDataset(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of Datasets."""

    succeeded: List[Dataset]
    failed: List[BulkUpdateFailed]


class CollectionAddressResponse(FidesSchema):
    """Schema for the representation of a collection in the graph"""

    dataset: Optional[str]
    collection: Optional[str]


class DryRunDatasetResponse(FidesSchema):
    """
    Response model for dataset dry run
    """

    collectionAddress: CollectionAddressResponse
    query: Any


class DatasetReachability(FidesSchema):
    """
    Response containing reachability details for a single dataset
    """

    reachable: bool
    details: Optional[Union[str, List[Dict[str, Any]]]]


class DatasetResponse(Dataset):
    """
    Dataset response model for API endpoints.

    Note: This class extends the Dataset model from fideslang rather than having a proper
    dedicated API response model. We had to make the collections field
    Optional and allow null values to support the minimal=true parameter in API responses,
    even though collections is required in the base fideslang Dataset model.
    """

    collections: Optional[List[DatasetCollection]] = Field(  # type: ignore
        description="An array of objects that describe the Dataset's collections.",
        default=None,
    )

    model_config = ConfigDict(
        extra="ignore", from_attributes=False, coerce_numbers_to_str=True
    )
