from typing import List

from pydantic import BaseModel, validator

from fideslang.models.fides_model import FidesModel, FidesKey
from fideslang.models.validation import sort_list_objects


class PrivacyRule(BaseModel):
    inclusion: str  # TODO make this an Enum of Any, All, None
    values: List[FidesKey]


class PolicyRule(FidesModel):
    dataCategories: PrivacyRule
    dataUses: PrivacyRule
    dataSubjects: PrivacyRule
    dataQualifier: FidesKey
    action: str  # TODO Make this an Enum or Reject or Approve


class Policy(FidesModel):
    rules: List[PolicyRule]

    _sort_rules = validator("rules", allow_reuse=True)(sort_list_objects)
