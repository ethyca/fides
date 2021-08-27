from typing import Dict, List, Optional

from pydantic import BaseModel, validator

from fidesctl.lang.validation import sort_list_objects
from fidesctl.lang.models.fides_model import FidesModel


class DatasetField(BaseModel):
    name: str
    description: str
    path: str
    dataCategories: Optional[List[str]]
    dataQualifier: Optional[str]


class Dataset(FidesModel):
    id: Optional[int]
    organizationId: int
    metadata: Optional[Dict[str, str]]
    name: str
    description: str
    dataCategories: Optional[List[str]]
    dataQualifier: Optional[str]
    location: str
    datasetType: str
    fields: List[DatasetField]

    @validator("fields")
    sort_list_objects(cls, values)
