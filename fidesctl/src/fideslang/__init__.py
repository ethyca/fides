"""
Exports various fideslang objects for easier use elsewhere.
"""

from typing import Dict, Type, Union

# Export the Models
from .models import (
    DataCategory,
    DataQualifier,
    DataSubject,
    DataUse,
    Dataset,
    DatasetField,
    Evaluation,
    FidesModel,
    Organization,
    Policy,
    PolicyRule,
    PrivacyRule,
    Registry,
    PrivacyDeclaration,
    System,
    Taxonomy,
)
from .default_taxonomy import DEFAULT_TAXONOMY

ModelTypeUnion = Union[Type[FidesModel], Type[Evaluation]]
model_map: Dict[str, ModelTypeUnion] = {
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
