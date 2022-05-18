"""
Exports various fideslang objects for easier use elsewhere.
"""

from typing import Dict, Type, Union

from .default_fixtures import COUNTRY_CODES
from .default_taxonomy import DEFAULT_TAXONOMY

# Export the Models
from .models import (
    DataCategory,
    DataQualifier,
    Dataset,
    DatasetField,
    DataSubject,
    DataUse,
    Evaluation,
    FidesModel,
    Organization,
    Policy,
    PolicyRule,
    PrivacyDeclaration,
    PrivacyRule,
    Registry,
    System,
    Taxonomy,
)

FidesModelType = Union[Type[FidesModel], Type[Evaluation]]
model_map: Dict[str, FidesModelType] = {
    "data_category": DataCategory,
    "data_qualifier": DataQualifier,
    "data_subject": DataSubject,
    "data_use": DataUse,
    "dataset": Dataset,
    "organization": Organization,
    "policy": Policy,
    "registry": Registry,
    "system": System,
    "evaluation": Evaluation,
}
model_list = list(model_map.keys())
