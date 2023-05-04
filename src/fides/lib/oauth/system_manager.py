from fides.api.ops.api.v1.scope_registry import SYSTEM_DELETE, SYSTEM_UPDATE

# System managers are separate from roles, because you are just granted these
# permissions to specific system(s) not to all resources of a given type
SYSTEM_MANAGER_SCOPES = [SYSTEM_UPDATE, SYSTEM_DELETE]
