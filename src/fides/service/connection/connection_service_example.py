"""
Example of how to refactor ConnectionService using audit decorators.
"""
from fides.api.schemas.event_audit import EventAuditType
from fides.service.connection.audit_decorators import (
    audit_connection_operation,
    audit_secrets_operation,
)


class ConnectionServiceRefactored:
    """Example of ConnectionService with audit decorators."""

    # BEFORE: Manual audit calls
    def delete_connection_old(self, connection_key: str):
        connection_config = self.get_connection_config(connection_key)

        # Manual audit event
        self._create_connection_audit_event(
            EventAuditType.connection_deleted,
            connection_config,
        )

        # Deletion logic...
        connection_config.delete(db=self.db)

    # AFTER: Automatic audit with decorator
    @audit_connection_operation(EventAuditType.connection_deleted)
    def delete_connection_new(self, connection_key: str):
        connection_config = self.get_connection_config(connection_key)
        # Deletion logic only - audit is automatic!
        connection_config.delete(db=self.db)
        return connection_config  # Decorator extracts this

    # BEFORE: Complex create/update logic
    def upsert_connection_old(self, connection_config):
        existing = self.get_connection_config(connection_config.key)

        # Save logic...
        connection_config.save(db=self.db)

        # Manual conditional audit
        event_type = (
            EventAuditType.connection_updated
            if existing
            else EventAuditType.connection_created
        )
        self._create_connection_audit_event(event_type, connection_config)

    # AFTER: Clean auto-detection
    @audit_connection_operation(
        'auto',
        on_create=EventAuditType.connection_created,
        on_update=EventAuditType.connection_updated
    )
    def upsert_connection_new(self, connection_config):
        # Just the business logic!
        connection_config.save(db=self.db)
        return connection_config

    # BEFORE: Secrets with manual audit
    def update_secrets_old(self, connection_config, secrets):
        # Update logic...
        connection_config.secrets = secrets
        connection_config.save(db=self.db)

        # Manual audit
        self._create_secrets_audit_event(
            EventAuditType.connection_secrets_updated,
            connection_config,
            secrets,
        )

    # AFTER: Automatic secrets audit
    @audit_secrets_operation(
        'auto',
        on_create=EventAuditType.connection_secrets_created,
        on_update=EventAuditType.connection_secrets_updated
    )
    def update_secrets_new(self, connection_config, secrets):
        # Just the business logic!
        connection_config.secrets = secrets
        connection_config.save(db=self.db)
        return connection_config
