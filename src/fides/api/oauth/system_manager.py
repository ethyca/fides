from fides.common.api.scope_registry import (
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_DELETE,
    CONNECTION_READ,
    SYSTEM_DELETE,
    SYSTEM_UPDATE,
)

# System managers are separate from roles, because you are just granted these
# permissions to specific system(s) not to all resources of a given type
SYSTEM_MANAGER_SCOPES = [
    SYSTEM_UPDATE,
    SYSTEM_DELETE,
    CONNECTION_CREATE_OR_UPDATE,
    CONNECTION_READ,
    CONNECTION_DELETE,
]
