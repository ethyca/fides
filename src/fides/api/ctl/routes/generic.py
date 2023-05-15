"""
Contains all of the generic CRUD endpoints that can be
generated programmatically for each resource.
"""

from typing import List

from fideslang import model_map

from fides.api.ctl.routes.generic_endpoint_utils import generic_router_factory
from fides.api.ctl.utils.api_router import APIRouter

routers: List[APIRouter] = []
for model_type, fides_model in model_map.items():
    routers += [generic_router_factory(fides_model=fides_model, model_type=model_type)]
