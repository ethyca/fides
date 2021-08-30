from typing import List, Optional

from pydantic import BaseModel, Field

from fideslang.models.data_category import DataCategory
from fideslang.models.data_qualifier import DataQualifier
from fideslang.models.data_subject import DataSubject
from fideslang.models.data_use import DataUse
from fideslang.models.dataset import Dataset
from fideslang.models.organization import Organization
from fideslang.models.policy import Policy
from fideslang.models.registry import Registry
from fideslang.models.system import System


class Taxonomy(BaseModel):
    "Represents an entire taxonomy of Fides Resources."

    data_categories: Optional[List[DataCategory]] = Field(alias="data-category")
    data_subjects: Optional[List[DataSubject]] = Field(alias="data-subject")
    data_uses: Optional[List[DataUse]] = Field(alias="data-use")
    data_qualifiers: Optional[List[DataQualifier]] = Field(alias="data-qualifier")

    datasets: Optional[List[Dataset]] = Field(alias="dataset")
    systems: Optional[List[System]] = Field(alias="system")
    policies: Optional[List[Policy]] = Field(alias="policy")

    registries: Optional[List[Registry]] = Field(alias="registry")
    organizations: Optional[List[Organization]] = Field(alias="organization")
