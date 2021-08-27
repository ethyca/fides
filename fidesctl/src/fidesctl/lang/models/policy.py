from typing import List, Optional

from pydantic import BaseModel, validator

from fidesctl.lang.models.fides_model import FidesModel


class PrivacyRule(BaseModel):
    inclusion: str
    values: List[str]


class PolicyRule(BaseModel):
    organizationId: int
    fidesKey: str
    name: str
    description: str
    dataCategories: PrivacyRule
    dataUses: PrivacyRule
    dataSubjects: PrivacyRule
    dataQualifier: str
    action: str


class Policy(FidesModel):
    id: Optional[int]
    organizationId: int
    fidesKey: str
    name: str
    description: str
    rules: List[PolicyRule]

    @validator("rules")
    def sort_list_objects(cls, v: List) -> List:
        v.sort(key=lambda x: x.name)
        return v
