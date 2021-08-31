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

    data_category: Optional[List[DataCategory]]
    data_subject: Optional[List[DataSubject]]
    data_use: Optional[List[DataUse]]
    data_qualifier: Optional[List[DataQualifier]]

    dataset: Optional[List[Dataset]]
    system: Optional[List[System]]
    policy: Optional[List[Policy]]

    registry: Optional[List[Registry]]
    organization: Optional[List[Organization]]
