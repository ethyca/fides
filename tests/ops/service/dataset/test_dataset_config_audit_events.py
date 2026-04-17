"""Tests for audit event emission in DatasetConfigService (SaaS scope)."""

from unittest.mock import MagicMock

import pytest
from fideslang.models import Dataset as FideslangDataset
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import AccessLevel, ConnectionConfig, ConnectionType
from fides.api.models.event_audit import EventAuditType
from fides.service.dataset.dataset_config_service import DatasetConfigService
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
