from fides.api.api.v1.endpoints import (
    config_endpoints,
    connection_endpoints,
    connection_type_endpoints,
    consent_request_endpoints,
    dataset_endpoints,
    drp_endpoints,
    encryption_endpoints,
    identity_verification_endpoints,
    manual_webhook_endpoints,
    masking_endpoints,
    messaging_endpoints,
    oauth_endpoints,
    policy_endpoints,
    policy_webhook_endpoints,
    privacy_experience_config_endpoints,
    privacy_request_endpoints,
    registration_endpoints,
    saas_config_endpoints,
    storage_endpoints,
    user_endpoints,
    user_permission_endpoints,
)
from fides.api.util.api_router import APIRouter

api_router = APIRouter()
api_router.include_router(config_endpoints.router)
api_router.include_router(connection_type_endpoints.router)
api_router.include_router(connection_endpoints.router)
api_router.include_router(consent_request_endpoints.router)
api_router.include_router(dataset_endpoints.router)
api_router.include_router(drp_endpoints.router)
api_router.include_router(encryption_endpoints.router)
api_router.include_router(masking_endpoints.router)
api_router.include_router(oauth_endpoints.router)
api_router.include_router(policy_endpoints.router)
api_router.include_router(policy_webhook_endpoints.router)
api_router.include_router(privacy_experience_config_endpoints.router)
api_router.include_router(privacy_request_endpoints.router)
api_router.include_router(identity_verification_endpoints.router)
api_router.include_router(storage_endpoints.router)
api_router.include_router(messaging_endpoints.router)
api_router.include_router(saas_config_endpoints.router)
api_router.include_router(user_endpoints.router)
api_router.include_router(user_permission_endpoints.router)
api_router.include_router(manual_webhook_endpoints.router)
api_router.include_router(registration_endpoints.router)
