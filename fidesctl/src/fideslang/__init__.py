from typing import Dict, Type

# Export the Models
from fideslang.models.data_category import DataCategory
from fideslang.models.data_qualifier import DataQualifier
from fideslang.models.data_subject import DataSubject
from fideslang.models.dataset import Dataset
from fideslang.models.dataset import DatasetField
from fideslang.models.data_use import DataUse
from fideslang.models.fides_model import FidesModel
from fideslang.models.organization import Organization
from fideslang.models.policy import Policy
from fideslang.models.policy import PolicyRule
from fideslang.models.registry import Registry
from fideslang.models.system import System
from fideslang.models.system import PrivacyDeclaration

model_map: Dict[str, Type[FidesModel]] = {
    "data-category": DataCategory,
    "data-qualifier": DataQualifier,
    "dataset": Dataset,
    "data-subject": DataSubject,
    "data-use": DataUse,
    "organization": Organization,
    "policy": Policy,
    "registry": Registry,
    "system": System,
}
model_list = list(model_map.keys())
