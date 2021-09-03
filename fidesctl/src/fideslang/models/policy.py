from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, validator

from fideslang.models.fides_model import FidesModel, FidesKey
from fideslang.models.validation import sort_list_objects


class InclusionEnum(str, Enum):
    ANY = "ANY"
    ALL = "ALL"
    NONE = "NONE"


class ActionEnum(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


class PrivacyRule(BaseModel):
    inclusion: InclusionEnum
    values: List[FidesKey]


class PolicyRule(FidesModel):
    dataCategories: PrivacyRule
    dataUses: PrivacyRule
    dataSubjects: PrivacyRule
    dataQualifier: FidesKey
    action: ActionEnum


class Policy(FidesModel):
    rules: List[PolicyRule]

    _sort_rules = validator("rules", allow_reuse=True)(sort_list_objects)
