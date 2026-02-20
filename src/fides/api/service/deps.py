"""
Re-export shim -- canonical location is fides.api.deps.
"""

from fides.api.deps import (  # noqa: F401
    get_connection_service,
    get_dataset_config_service,
    get_dataset_service,
    get_event_audit_service,
    get_messaging_service,
    get_privacy_request_service,
    get_system_service,
    get_taxonomy_service,
    get_user_service,
)
