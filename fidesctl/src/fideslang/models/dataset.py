from typing import Dict, List, Optional

from pydantic import BaseModel, validator

from fideslang.models.validation import sort_list_objects
from fideslang.models.fides_model import FidesModel, FidesKey


class DatasetField(BaseModel):
    name: str
    description: str
    path: str
    dataCategories: Optional[List[FidesKey]]
    dataQualifier: Optional[FidesKey]


class Dataset(FidesModel):
    metadata: Optional[Dict[str, str]]
    dataCategories: Optional[List[FidesKey]]
    dataQualifier: Optional[FidesKey]
    location: str
    datasetType: str
    fields: List[DatasetField]

    _sort_fields = validator("fields", allow_reuse=True)(sort_list_objects)
