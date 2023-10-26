"""
This module generates all of the routers for the boilerplate/generic
objects that don't require any extra logic.
"""
from fideslang.models import Dataset, Evaluation, Organization, Policy, Registry

from fides.api.schemas.taxonomy_extensions import (
    DataCategory,
    DataQualifier,
    DataSubject,
    DataUse,
)

from .router_factory import generic_router_factory  # type: ignore[attr-defined]

DATA_CATEGORY_ROUTER = generic_router_factory(
    fides_model=DataCategory, model_type="data_category"
)
DATA_USE_ROUTER = generic_router_factory(fides_model=DataUse, model_type="data_use")
DATA_SUBJECT_ROUTER = generic_router_factory(
    fides_model=DataSubject, model_type="data_subject"
)
DATA_QUALIFIER_ROUTER = generic_router_factory(
    fides_model=DataQualifier, model_type="data_qualifier"
)
DATASET_ROUTER = generic_router_factory(fides_model=Dataset, model_type="dataset")
ORGANIZATION_ROUTER = generic_router_factory(
    fides_model=Organization, model_type="organization"
)
POLICY_ROUTER = generic_router_factory(fides_model=Policy, model_type="policy")
REGISTRY_ROUTER = generic_router_factory(fides_model=Registry, model_type="registry")
EVALUATION_ROUTER = generic_router_factory(
    fides_model=Evaluation, model_type="evaluation"
)
