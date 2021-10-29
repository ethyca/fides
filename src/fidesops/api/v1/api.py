from fastapi import APIRouter

from fidesops.api.v1.endpoints import (
    config_endpoints,
    connection_endpoints,
    dataset_endpoints,
    encryption_endpoints,
    health_endpoints,
    masking_endpoints,
    oauth_endpoints,
    policy_endpoints,
    privacy_request_endpoints,
    storage_endpoints,
)


api_router = APIRouter()
api_router.include_router(config_endpoints.router)
api_router.include_router(connection_endpoints.router)
api_router.include_router(dataset_endpoints.router)
api_router.include_router(encryption_endpoints.router)
api_router.include_router(health_endpoints.router)
api_router.include_router(masking_endpoints.router)
api_router.include_router(oauth_endpoints.router)
api_router.include_router(policy_endpoints.router)
api_router.include_router(privacy_request_endpoints.router)
api_router.include_router(storage_endpoints.router)
