"""Shared fixtures for service-level tests."""

from typing import Any, Dict

import pytest
from sqlalchemy.orm import Session

from fides.api.request_context import reset_request_context, set_user_id
from fides.service.connection.connection_service import ConnectionService
from fides.service.event_audit_service import EventAuditService


@pytest.fixture
def event_audit_service(db: Session):
    """Fixture to provide EventAuditService instance with database session."""
    return EventAuditService(db)


@pytest.fixture
def sample_event_details() -> Dict[str, Any]:
    """Sample event details for testing."""
    return {
        "action": "create",
        "resource_name": "test_resource",
        "properties": {"name": "example_name", "description": "example_description"},
        "metadata": {"ip_address": "192.168.1.1", "user_agent": "test-agent"},
    }


@pytest.fixture
def request_context_user_id():
    """Fixture that sets a user_id in the request context and cleans up after test."""
    test_user_id = "context_user_123"
    set_user_id(test_user_id)
    yield test_user_id
    reset_request_context()  # Clean up after test


@pytest.fixture
def connection_service(db, event_audit_service):
    """ConnectionService instance with mocked dependencies."""
    return ConnectionService(db, event_audit_service)
