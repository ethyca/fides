from typing import Dict, Type

# Export the Models
from fideslang.models.data_category import DataCategory
from fideslang.models.data_qualifier import DataQualifier
from fideslang.models.data_subject import DataSubject
from fideslang.models.data_use import DataUse
from fideslang.models.dataset import Dataset, DatasetField
from fideslang.models.evaluation import Evaluation
from fideslang.models.fides_model import FidesModel
from fideslang.models.organization import Organization
from fideslang.models.policy import Policy, PolicyRule, PrivacyRule
from fideslang.models.registry import Registry
from fideslang.models.system import PrivacyDeclaration, System
from fideslang.models.taxonomy import Taxonomy

model_map: Dict[str, Type[FidesModel]] = {
    "data_category": DataCategory,
    "data_qualifier": DataQualifier,
    "data_subject": DataSubject,
    "data_use": DataUse,
    "dataset": Dataset,
    "organization": Organization,
    "policy": Policy,
    "registry": Registry,
    "system": System,
}
model_list = list(model_map.keys())
