from typing import List, Optional

from pydantic import BaseModel, validator

from fideslang.models.fides_model import FidesModel


class PrivacyRule(BaseModel):
    inclusion: str
    values: List[str]


class PolicyRule(FidesModel):
    dataCategories: PrivacyRule
    dataUses: PrivacyRule
    dataSubjects: PrivacyRule
    dataQualifier: str
    action: str


class Policy(FidesModel):
    rules: List[PolicyRule]

    @validator("rules")
    def sort_list_objects(cls, v: List) -> List:
        v.sort(key=lambda x: x.name)
        return v
