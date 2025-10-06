"""
Decorators for automatic audit event creation in connection operations.
"""
from functools import wraps
from typing import Any, Callable, Optional, Union

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.event_audit import EventAuditType


def audit_connection_operation(
    event_type: Union[EventAuditType, str],
    *,
    on_create: Optional[EventAuditType] = None,
    on_update: Optional[EventAuditType] = None,
    extract_connection: str = "connection_config",
    condition: Optional[str] = None,
):
    """
    Decorator to automatically create audit events for connection operations.

    Args:
        event_type: Fixed event type, or 'auto' for create/update detection
        on_create: Event type when creating (used with event_type='auto')
        on_update: Event type when updating (used with event_type='auto')
        extract_connection: Parameter name containing ConnectionConfig
        condition: Optional condition to check before creating event

    Example:
        @audit_connection_operation(EventAuditType.connection_deleted)
        def delete_connection(self, connection_key: str):
            # ... deletion logic

        @audit_connection_operation(
            'auto',
            on_create=EventAuditType.connection_created,
            on_update=EventAuditType.connection_updated
        )
        def upsert_connection(self, connection_config: ConnectionConfig):
            # ... upsert logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Execute the original function first
            result = func(self, *args, **kwargs)

            # Extract connection_config from parameters
            connection_config = None

            # Try to get from kwargs first
            if extract_connection in kwargs:
                connection_config = kwargs[extract_connection]
            else:
                # Try to get from args based on function signature
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())[1:]  # Skip 'self'

                if extract_connection in param_names:
                    param_index = param_names.index(extract_connection)
                    if param_index < len(args):
                        connection_config = args[param_index]

            if not connection_config or not isinstance(connection_config, ConnectionConfig):
                return result

            # Check condition if provided
            if condition:
                if not getattr(self, condition, lambda: True)():
                    return result

            # Determine event type
            final_event_type = event_type
            if event_type == 'auto':
                # Auto-detect create vs update
                existing = getattr(connection_config, 'id', None) is not None
                final_event_type = on_update if existing else on_create

            # Create audit event
            if hasattr(self, '_create_connection_audit_event'):
                self._create_connection_audit_event(
                    final_event_type,
                    connection_config,
                )

            return result
        return wrapper
    return decorator


def audit_secrets_operation(
    event_type: Union[EventAuditType, str],
    *,
    on_create: Optional[EventAuditType] = None,
    on_update: Optional[EventAuditType] = None,
    extract_connection: str = "connection_config",
    extract_secrets: str = "secrets",
):
    """
    Decorator for secrets audit events.

    Example:
        @audit_secrets_operation(
            'auto',
            on_create=EventAuditType.connection_secrets_created,
            on_update=EventAuditType.connection_secrets_updated
        )
        def update_secrets(self, connection_config, secrets):
            # ... secrets logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)

            # Extract parameters (similar logic as above)
            connection_config = kwargs.get(extract_connection)
            secrets = kwargs.get(extract_secrets)

            if not connection_config or not secrets:
                return result

            # Determine event type
            final_event_type = event_type
            if event_type == 'auto':
                existing = getattr(connection_config, 'id', None) is not None
                final_event_type = on_update if existing else on_create

            # Create secrets audit event
            if hasattr(self, '_create_secrets_audit_event'):
                self._create_secrets_audit_event(
                    final_event_type,
                    connection_config,
                    secrets,
                )

            return result
        return wrapper
    return decorator
