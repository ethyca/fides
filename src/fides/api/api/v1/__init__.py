"""
Define routes for the ctl-related objects.

All routes should get imported here and added to the CTL_ROUTER
"""
from fastapi import APIRouter

from .endpoints.admin import ADMIN_ROUTER
from .endpoints.generate import GENERATE_ROUTER
from .endpoints.generic import (
    DATA_CATEGORY_ROUTER,
    DATA_QUALIFIER_ROUTER,
    DATA_SUBJECT_ROUTER,
    DATA_USE_ROUTER,
    DATASET_ROUTER,
    EVALUATION_ROUTER,
    ORGANIZATION_ROUTER,
    POLICY_ROUTER,
    REGISTRY_ROUTER,
)
from .endpoints.health import HEALTH_ROUTER
from .endpoints.system import (
    SYSTEM_CONNECTION_INSTANTIATE_ROUTER,
    SYSTEM_CONNECTIONS_ROUTER,
    SYSTEM_ROUTER,
)
from .endpoints.validate import VALIDATE_ROUTER

routers = [
    ADMIN_ROUTER,
    DATA_CATEGORY_ROUTER,
    DATA_SUBJECT_ROUTER,
    DATA_QUALIFIER_ROUTER,
    DATA_USE_ROUTER,
    DATASET_ROUTER,
    EVALUATION_ROUTER,
    GENERATE_ROUTER,
    HEALTH_ROUTER,
    ORGANIZATION_ROUTER,
    POLICY_ROUTER,
    REGISTRY_ROUTER,
    SYSTEM_CONNECTION_INSTANTIATE_ROUTER,
    SYSTEM_CONNECTIONS_ROUTER,
    SYSTEM_ROUTER,
    VALIDATE_ROUTER,
]

CTL_ROUTER = APIRouter()
for router in routers:
    CTL_ROUTER.include_router(router)
