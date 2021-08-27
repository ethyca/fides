from typing import Dict, Type

from fidesctl.lang.models.data_category import DataCategory
from fidesctl.lang.models.data_qualifier import DataQualifier
from fidesctl.lang.models.data_subject import DataSubject
from fidesctl.lang.models.data_use import DataUse
from fidesctl.lang.models.dataset import Dataset
from fidesctl.lang.models.fides_model import FidesModel
from fidesctl.lang.models.organization import Organization
from fidesctl.lang.models.policy import Policy
from fidesctl.lang.models.registry import Registry
from fidesctl.lang.models.system import System

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
