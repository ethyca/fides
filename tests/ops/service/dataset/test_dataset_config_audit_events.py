"""Tests for audit event emission in DatasetConfigService (SaaS scope)."""

from unittest.mock import MagicMock

import pytest
from fideslang.models import Dataset as FideslangDataset
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.event_audit import EventAudit, EventAuditType
from fides.service.dataset.dataset_config_service import DatasetConfigService
from fides.service.dataset.dataset_service import DatasetNotFoundException
from fides.service.event_audit_service import EventAuditService

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

_SAAS_FIDES_KEY = "audit_test_saas_ds"

_MINIMAL_SAAS_CONFIG = {
    "fides_key": _SAAS_FIDES_KEY,
    "name": "Audit Test Connector",
    "type": "audit_test_connector",
    "description": "Minimal SaaS config for audit tests",
    "version": "0.1.0",
    "connector_params": [],
    "client_config": {"protocol": "https", "host": "api.example.com"},
    "test_request": {"method": "GET", "path": "/test"},
    "endpoints": [],
}

_MINIMAL_DATASET = FideslangDataset.model_validate(
    {
        "fides_key": _SAAS_FIDES_KEY,
        "name": "Audit Test Dataset",
        "collections": [
            {
                "name": "items",
                "fields": [{"name": "id", "data_categories": ["system.operations"]}],
            }
        ],
    }
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDatasetConfigServiceAuditEvents:
    @pytest.fixture(autouse=True)
    def clean_audit_events(self, db: Session) -> None:
        db.query(EventAudit).filter(
            EventAudit.resource_type == "dataset_config",
            EventAudit.resource_identifier.in_([_SAAS_FIDES_KEY, "audit_test_postgres_ds"]),
        ).delete(synchronize_session=False)
        db.commit()

    @pytest.fixture
    def saas_connection_config(self, db: Session) -> ConnectionConfig:
        config = ConnectionConfig.create(
            db=db,
            data={
                "key": "audit_test_saas_connection",
                "name": "Audit Test SaaS Connection",
                "connection_type": ConnectionType.saas,
                "access": AccessLevel.write,
                "saas_config": _MINIMAL_SAAS_CONFIG,
            },
        )
        yield config
        config.delete(db)

    @pytest.fixture
    def postgres_connection_config(self, db: Session) -> ConnectionConfig:
        config = ConnectionConfig.create(
            db=db,
            data={
                "key": "audit_test_postgres_connection",
                "name": "Audit Test Postgres Connection",
                "connection_type": ConnectionType.postgres,
                "access": AccessLevel.write,
            },
        )
        yield config
        config.delete(db)

    @pytest.fixture
    def service(self, db: Session) -> DatasetConfigService:
        return DatasetConfigService(db, EventAuditService(db))

    def test_create_saas_dataset_emits_created_event(
        self,
        db: Session,
        service: DatasetConfigService,
        saas_connection_config: ConnectionConfig,
    ):
        """First upsert of a dataset on a SaaS connection emits dataset.created."""
        service.create_or_update_dataset_config(saas_connection_config, _MINIMAL_DATASET)

        events = EventAuditService(db).get_events_for_resource(
            "dataset_config", _SAAS_FIDES_KEY
        )
        assert len(events) == 1
        assert events[0].event_type == EventAuditType.dataset_created.value
        assert events[0].resource_identifier == _SAAS_FIDES_KEY
        assert events[0].event_details["operation_type"] == "created"
        assert events[0].event_details["connection_key"] == saas_connection_config.key
        assert events[0].event_details["saas_connector_type"] == "audit_test_connector"

    def test_update_saas_dataset_emits_updated_event(
        self,
        db: Session,
        service: DatasetConfigService,
        saas_connection_config: ConnectionConfig,
    ):
        """Second upsert of the same dataset key emits dataset.updated."""
        service.create_or_update_dataset_config(saas_connection_config, _MINIMAL_DATASET)
        service.create_or_update_dataset_config(saas_connection_config, _MINIMAL_DATASET)

        events = EventAuditService(db).get_events_for_resource(
            "dataset_config", _SAAS_FIDES_KEY
        )
        assert len(events) == 2
        # get_events_for_resource returns newest-first
        assert events[0].event_type == EventAuditType.dataset_updated.value
        assert events[1].event_type == EventAuditType.dataset_created.value

    def test_delete_saas_dataset_emits_deleted_event(
        self,
        db: Session,
        service: DatasetConfigService,
        saas_connection_config: ConnectionConfig,
    ):
        """Deleting a SaaS dataset config emits dataset.deleted."""
        service.create_or_update_dataset_config(saas_connection_config, _MINIMAL_DATASET)
        service.delete_dataset_config(saas_connection_config, _SAAS_FIDES_KEY)

        events = EventAuditService(db).get_events_for_resource(
            "dataset_config", _SAAS_FIDES_KEY
        )
        assert len(events) == 2
        # get_events_for_resource returns newest-first
        assert events[0].event_type == EventAuditType.dataset_deleted.value
        assert events[0].event_details["operation_type"] == "deleted"

    def test_non_saas_dataset_no_audit_event(
        self,
        db: Session,
        service: DatasetConfigService,
        postgres_connection_config: ConnectionConfig,
    ):
        """Mutations on a non-SaaS connection produce no audit events."""
        dataset = FideslangDataset.model_validate(
            {
                "fides_key": "audit_test_postgres_ds",
                "name": "Audit Test Postgres Dataset",
                "collections": [
                    {
                        "name": "items",
                        "fields": [
                            {"name": "id", "data_categories": ["system.operations"]}
                        ],
                    }
                ],
            }
        )
        service.create_or_update_dataset_config(postgres_connection_config, dataset)

        events = EventAuditService(db).get_events_for_resource(
            "dataset_config", "audit_test_postgres_ds"
        )
        assert events == []

    def test_audit_failure_does_not_raise(
        self,
        db: Session,
        saas_connection_config: ConnectionConfig,
    ):
        """A broken audit service must not surface errors to the caller."""
        broken_audit_service = MagicMock(spec=EventAuditService)
        broken_audit_service.create_event_audit.side_effect = Exception("audit boom")

        service = DatasetConfigService(db, broken_audit_service)
        result, error = service.create_or_update_dataset_config(
            saas_connection_config, _MINIMAL_DATASET
        )
        assert result is not None
        assert error is None

    def test_no_audit_service_does_not_raise(
        self,
        db: Session,
        saas_connection_config: ConnectionConfig,
    ):
        """When no EventAuditService is injected, create/update succeeds silently."""
        service = DatasetConfigService(db, event_audit_service=None)
        result, error = service.create_or_update_dataset_config(
            saas_connection_config, _MINIMAL_DATASET
        )
        assert result is not None
        assert error is None
        # No audit rows should exist since there is no service
        events = EventAuditService(db).get_events_for_resource(
            "dataset_config", _SAAS_FIDES_KEY
        )
        assert events == []

    def test_delete_audit_failure_does_not_raise(
        self,
        db: Session,
        service: DatasetConfigService,
        saas_connection_config: ConnectionConfig,
    ):
        """A broken audit service on delete must not surface errors to the caller."""
        service.create_or_update_dataset_config(saas_connection_config, _MINIMAL_DATASET)

        broken_audit_service = MagicMock(spec=EventAuditService)
        broken_audit_service.create_event_audit.side_effect = Exception("audit boom")
        broken_service = DatasetConfigService(db, broken_audit_service)
        broken_service.delete_dataset_config(saas_connection_config, _SAAS_FIDES_KEY)  # must not raise

    def test_delete_no_audit_service_does_not_raise(
        self,
        db: Session,
        saas_connection_config: ConnectionConfig,
    ):
        """When no EventAuditService is injected, delete succeeds silently."""
        DatasetConfigService(db, EventAuditService(db)).create_or_update_dataset_config(
            saas_connection_config, _MINIMAL_DATASET
        )
        service = DatasetConfigService(db, event_audit_service=None)
        service.delete_dataset_config(saas_connection_config, _SAAS_FIDES_KEY)  # must not raise

        events = EventAuditService(db).get_events_for_resource(
            "dataset_config", _SAAS_FIDES_KEY
        )
        assert all(e.event_type != EventAuditType.dataset_deleted.value for e in events)

    def test_delete_non_saas_no_audit_event(
        self,
        db: Session,
        service: DatasetConfigService,
        postgres_connection_config: ConnectionConfig,
    ):
        """Deleting a non-SaaS dataset config emits no audit event."""
        pg_key = "audit_test_postgres_ds"
        dataset = FideslangDataset.model_validate(
            {
                "fides_key": pg_key,
                "name": "Audit Test Postgres Dataset",
                "collections": [
                    {
                        "name": "items",
                        "fields": [
                            {"name": "id", "data_categories": ["system.operations"]}
                        ],
                    }
                ],
            }
        )
        service.create_or_update_dataset_config(postgres_connection_config, dataset)
        service.delete_dataset_config(postgres_connection_config, pg_key)

        events = EventAuditService(db).get_events_for_resource("dataset_config", pg_key)
        assert events == []

    def test_delete_nonexistent_dataset_raises(
        self,
        db: Session,
        service: DatasetConfigService,
        saas_connection_config: ConnectionConfig,
    ):
        """Deleting a dataset_key that does not exist raises DatasetNotFoundException."""
        with pytest.raises(DatasetNotFoundException, match="no_such_key"):
            service.delete_dataset_config(saas_connection_config, "no_such_key")
