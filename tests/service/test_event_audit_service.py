import pytest

from fides.api.models.event_audit import EventAudit, EventAuditStatus, EventAuditType


class TestCreateEventAudit:
    """Tests for creating EventAudit records via EventAuditService."""

    def test_create_event_audit_with_all_fields(
        self, db, event_audit_service, sample_event_details
    ):
        """Test creating event audit with all fields populated."""
        event_audit = event_audit_service.create_event_audit(
            event_type=EventAuditType.system_updated,
            status=EventAuditStatus.succeeded,
            user_id="test_user_123",
            resource_type="system",
            resource_identifier="sys_456",
            description="Updated system configuration",
            event_details=sample_event_details,
        )

        assert event_audit is not None
        assert event_audit.event_type == EventAuditType.system_updated.value
        assert event_audit.user_id == "test_user_123"
        assert event_audit.resource_type == "system"
        assert event_audit.resource_identifier == "sys_456"
        assert event_audit.description == "Updated system configuration"
        assert event_audit.event_details == sample_event_details
        assert event_audit.created_at is not None
        assert event_audit.updated_at is not None

    def test_create_event_audit_with_minimal_fields(self, db, event_audit_service):
        """Test creating event audit with only required fields."""
        event_audit = event_audit_service.create_event_audit(
            event_type=EventAuditType.taxonomy_element_created,
            status=EventAuditStatus.succeeded,
        )

        assert event_audit is not None
        assert event_audit.event_type == EventAuditType.taxonomy_element_created.value
        assert (
            event_audit.user_id is None
        )  # get_user_id() returns None when no context set
        assert event_audit.resource_type is None
        assert event_audit.resource_identifier is None
        assert event_audit.description is None
        assert event_audit.event_details is None

    def test_create_event_audit_uses_request_context_user_id(
        self, db, event_audit_service, request_context_user_id
    ):
        """Test that create_event_audit uses user_id from request context when no explicit user_id provided."""
        event_audit = event_audit_service.create_event_audit(
            event_type=EventAuditType.system_group_created,
            status=EventAuditStatus.succeeded,
        )

        # Should use the user_id from request context
        assert event_audit.user_id == request_context_user_id
        assert event_audit.user_id == "context_user_123"

    def test_create_event_audit_prefers_provided_user_id(
        self, db, event_audit_service, request_context_user_id
    ):
        """Test that create_event_audit uses explicit user_id instead of request context."""
        event_audit = event_audit_service.create_event_audit(
            event_type=EventAuditType.system_group_updated,
            status=EventAuditStatus.succeeded,
            user_id="explicit_user",
        )

        # Should use explicit user_id, not the one from request context
        assert event_audit.user_id == "explicit_user"
        assert event_audit.user_id != request_context_user_id

    @pytest.mark.parametrize(
        "event_type",
        [
            EventAuditType.system_updated,
            EventAuditType.system_group_created,
            EventAuditType.system_group_updated,
            EventAuditType.system_group_deleted,
            EventAuditType.taxonomy_created,
            EventAuditType.taxonomy_updated,
            EventAuditType.taxonomy_deleted,
            EventAuditType.taxonomy_usage_updated,
            EventAuditType.taxonomy_usage_deleted,
            EventAuditType.taxonomy_element_created,
            EventAuditType.taxonomy_element_updated,
            EventAuditType.taxonomy_element_deleted,
        ],
    )
    def test_create_event_audit_with_all_event_types(
        self, db, event_audit_service, event_type
    ):
        """Test creating event audits with all available EventAuditType values."""
        event_audit = event_audit_service.create_event_audit(
            event_type=event_type,
            status=EventAuditStatus.succeeded,
            resource_type="test_resource",
            resource_identifier="test_123",
            description=f"Test event for {event_type.value}",
        )

        assert event_audit is not None
        assert event_audit.event_type == event_type.value
        assert event_audit.resource_type == "test_resource"
        assert event_audit.resource_identifier == "test_123"

    def test_create_event_audit_with_complex_event_details(
        self, db, event_audit_service
    ):
        """Test creating event audit with complex nested event_details."""
        complex_details = {
            "operation": "bulk_update",
            "affected_items": [
                {"id": "item_1", "changes": {"name": "new_name_1"}},
                {"id": "item_2", "changes": {"status": "active"}},
            ],
            "validation_results": {
                "passed": True,
                "warnings": ["Minor issue detected"],
                "errors": [],
            },
            "performance": {"duration_ms": 1250, "memory_usage_mb": 45.2},
        }

        event_audit = event_audit_service.create_event_audit(
            event_type=EventAuditType.taxonomy_updated,
            status=EventAuditStatus.succeeded,
            event_details=complex_details,
        )

        assert event_audit.event_details == complex_details
        assert event_audit.event_details["operation"] == "bulk_update"
        assert len(event_audit.event_details["affected_items"]) == 2
        assert event_audit.event_details["validation_results"]["passed"] is True

    def test_create_event_audit_persisted_to_database(self, db, event_audit_service):
        """Test that created event audit is properly persisted to database."""
        event_audit = event_audit_service.create_event_audit(
            event_type=EventAuditType.system_group_deleted,
            status=EventAuditStatus.succeeded,
            resource_identifier="persistent_test",
        )

        # Verify it's persisted by querying database directly
        saved_audit = (
            db.query(EventAudit)
            .filter(EventAudit.resource_identifier == "persistent_test")
            .first()
        )

        assert saved_audit is not None
        assert saved_audit.id == event_audit.id
        assert saved_audit.event_type == EventAuditType.system_group_deleted.value


class TestEventAuditServiceQueries:
    """Tests for EventAuditService query methods."""

    @pytest.fixture
    def sample_events(self, db, event_audit_service):
        """Create sample events for query testing."""
        events = []

        # Create events for different resources
        events.append(
            event_audit_service.create_event_audit(
                event_type=EventAuditType.system_updated,
                status=EventAuditStatus.succeeded,
                user_id="user_1",
                resource_type="system",
                resource_identifier="sys_1",
                description="System 1 updated",
            )
        )

        events.append(
            event_audit_service.create_event_audit(
                event_type=EventAuditType.system_group_created,
                status=EventAuditStatus.succeeded,
                user_id="user_1",
                resource_type="system_group",
                resource_identifier="group_1",
                description="System group 1 created",
            )
        )

        events.append(
            event_audit_service.create_event_audit(
                event_type=EventAuditType.system_group_updated,
                status=EventAuditStatus.succeeded,
                user_id="user_2",
                resource_type="system_group",
                resource_identifier="group_1",
                description="System group 1 updated",
            )
        )

        events.append(
            event_audit_service.create_event_audit(
                event_type=EventAuditType.taxonomy_element_created,
                status=EventAuditStatus.succeeded,
                user_id="user_2",
                resource_type="taxonomy_element",
                resource_identifier="elem_1",
                description="Taxonomy element created",
            )
        )

        return events

    def test_get_events_for_resource_with_identifier(
        self, db, event_audit_service, sample_events
    ):
        """Test getting events for specific resource type and identifier."""
        events = event_audit_service.get_events_for_resource(
            resource_type="system_group", resource_identifier="group_1"
        )

        assert len(events) == 2
        assert all(e.resource_type == "system_group" for e in events)
        assert all(e.resource_identifier == "group_1" for e in events)
        # Should be ordered by created_at desc
        assert events[0].event_type == EventAuditType.system_group_updated.value
        assert events[1].event_type == EventAuditType.system_group_created.value

    def test_get_events_for_resource_type_only(
        self, db, event_audit_service, sample_events
    ):
        """Test getting events for resource type without specific identifier."""
        events = event_audit_service.get_events_for_resource(
            resource_type="system_group"
        )

        assert len(events) == 2
        assert all(e.resource_type == "system_group" for e in events)

    def test_get_events_for_resource_with_limit(
        self, db, event_audit_service, sample_events
    ):
        """Test getting events with limit parameter."""
        events = event_audit_service.get_events_for_resource(
            resource_type="system_group", limit=1
        )

        assert len(events) == 1
        # Should get most recent (system_group_updated)
        assert events[0].event_type == EventAuditType.system_group_updated.value

    def test_get_events_for_nonexistent_resource(
        self, db, event_audit_service, sample_events
    ):
        """Test getting events for resource that doesn't exist."""
        events = event_audit_service.get_events_for_resource(
            resource_type="nonexistent", resource_identifier="missing"
        )

        assert len(events) == 0

    def test_get_events_by_user(self, db, event_audit_service, sample_events):
        """Test getting events by specific user."""
        user_1_events = event_audit_service.get_events_by_user("user_1")
        user_2_events = event_audit_service.get_events_by_user("user_2")

        assert len(user_1_events) == 2
        assert len(user_2_events) == 2
        assert all(e.user_id == "user_1" for e in user_1_events)
        assert all(e.user_id == "user_2" for e in user_2_events)

    def test_get_events_by_user_with_limit(
        self, db, event_audit_service, sample_events
    ):
        """Test getting events by user with limit."""
        events = event_audit_service.get_events_by_user("user_2", limit=1)

        assert len(events) == 1
        assert events[0].user_id == "user_2"

    def test_get_events_by_nonexistent_user(
        self, db, event_audit_service, sample_events
    ):
        """Test getting events by user that doesn't exist."""
        events = event_audit_service.get_events_by_user("nonexistent_user")

        assert len(events) == 0

    def test_get_events_by_type(self, db, event_audit_service, sample_events):
        """Test getting events by specific event type."""
        system_events = event_audit_service.get_events_by_type(
            EventAuditType.system_updated
        )
        group_created_events = event_audit_service.get_events_by_type(
            EventAuditType.system_group_created
        )

        assert len(system_events) == 1
        assert len(group_created_events) == 1
        assert system_events[0].event_type == EventAuditType.system_updated.value
        assert (
            group_created_events[0].event_type
            == EventAuditType.system_group_created.value
        )

    def test_get_events_by_type_with_limit(
        self, db, event_audit_service, sample_events
    ):
        """Test getting events by type with limit."""
        events = event_audit_service.get_events_by_type(
            EventAuditType.system_group_created, limit=1
        )

        assert len(events) == 1
        assert events[0].event_type == EventAuditType.system_group_created.value

    def test_get_events_by_nonexistent_type(
        self, db, event_audit_service, sample_events
    ):
        """Test getting events by event type that has no records."""
        # Using taxonomy_deleted which wasn't created in sample_events
        events = event_audit_service.get_events_by_type(EventAuditType.taxonomy_deleted)

        assert len(events) == 0

    def test_get_events_by_category(self, db, event_audit_service, sample_events):
        """Test getting events by category prefix."""
        system_category_events = event_audit_service.get_events_by_category("system")
        system_group_category_events = event_audit_service.get_events_by_category(
            "system_group"
        )
        taxonomy_category_events = event_audit_service.get_events_by_category(
            "taxonomy"
        )

        # Should include only system.updated (system_group is a separate category)
        assert len(system_category_events) == 1
        assert (
            system_category_events[0].event_type == EventAuditType.system_updated.value
        )

        # Should include system_group.created and system_group.updated
        assert len(system_group_category_events) == 2
        system_group_event_types = {e.event_type for e in system_group_category_events}
        expected_system_group_types = {
            EventAuditType.system_group_created.value,
            EventAuditType.system_group_updated.value,
        }
        assert system_group_event_types == expected_system_group_types

        # Should include taxonomy.element.created
        assert len(taxonomy_category_events) == 1
        assert (
            taxonomy_category_events[0].event_type
            == EventAuditType.taxonomy_element_created.value
        )

    def test_get_events_by_category_with_limit(
        self, db, event_audit_service, sample_events
    ):
        """Test getting events by category with limit."""
        events = event_audit_service.get_events_by_category("system_group", limit=1)

        assert len(events) == 1
        # Should be ordered by created_at desc, so get the most recent system_group event
        assert events[0].event_type == EventAuditType.system_group_updated.value

    def test_get_events_by_nonexistent_category(
        self, db, event_audit_service, sample_events
    ):
        """Test getting events by category that doesn't exist."""
        events = event_audit_service.get_events_by_category("nonexistent")

        assert len(events) == 0

    def test_query_methods_return_ordered_results(self, db, event_audit_service):
        """Test that query methods return results ordered by created_at descending."""
        # Create events with slight delay to ensure different timestamps
        import time

        first_event = event_audit_service.create_event_audit(
            event_type=EventAuditType.system_updated,
            status=EventAuditStatus.succeeded,
            description="First event",
        )

        time.sleep(0.01)  # Small delay to ensure different timestamps

        second_event = event_audit_service.create_event_audit(
            event_type=EventAuditType.system_updated,
            status=EventAuditStatus.succeeded,
            description="Second event",
        )

        events = event_audit_service.get_events_by_type(EventAuditType.system_updated)

        assert len(events) == 2
        # Most recent should be first
        assert events[0].description == "Second event"
        assert events[1].description == "First event"
        assert events[0].created_at >= events[1].created_at


class TestEventAuditModelDirect:
    """Tests for EventAudit model direct creation (not via service)."""

    def test_event_audit_model_create_with_data_dict(self, db):
        """Test EventAudit.create() method with data dictionary."""
        event_data = {
            "event_type": EventAuditType.taxonomy_created.value,
            "status": EventAuditStatus.succeeded,
            "user_id": "direct_user",
            "resource_type": "taxonomy",
            "resource_identifier": "tax_123",
            "description": "Direct model creation",
            "event_details": {"method": "direct"},
        }

        event_audit = EventAudit.create(db=db, data=event_data)

        assert event_audit is not None
        assert event_audit.event_type == EventAuditType.taxonomy_created.value
        assert event_audit.user_id == "direct_user"
        assert event_audit.resource_type == "taxonomy"
        assert event_audit.resource_identifier == "tax_123"
        assert event_audit.description == "Direct model creation"
        assert event_audit.event_details == {"method": "direct"}

    def test_event_audit_model_create_minimal_data(self, db):
        """Test EventAudit.create() with minimal required data."""
        event_data = {
            "event_type": EventAuditType.system_group_created.value,
            "status": EventAuditStatus.succeeded,
        }

        event_audit = EventAudit.create(db=db, data=event_data)

        assert event_audit is not None
        assert event_audit.event_type == EventAuditType.system_group_created.value
        assert event_audit.user_id is None
        assert event_audit.resource_type is None
        assert event_audit.resource_identifier is None
        assert event_audit.description is None
        assert event_audit.event_details is None

    def test_event_audit_model_tablename(self):
        """Test that EventAudit model has correct table name."""
        assert EventAudit.__tablename__ == "event_audit"

    def test_event_audit_model_indexes(self, db):
        """Test that EventAudit model has proper database indexes."""
        # This is more of a database schema test, but we can verify the columns are indexed
        # by checking the model definition
        assert EventAudit.event_type.index is True
        assert EventAudit.user_id.index is True
        assert EventAudit.resource_type.index is True
        assert EventAudit.resource_identifier.index is True


class TestEventAuditTypeEnum:
    """Tests for EventAuditType enum completeness."""

    def test_all_event_audit_types_have_proper_hierarchy(self):
        """Test that all EventAuditType values follow proper hierarchical naming."""
        expected_patterns = {
            "system.": [EventAuditType.system_updated],
            "system_group.": [
                EventAuditType.system_group_created,
                EventAuditType.system_group_updated,
                EventAuditType.system_group_deleted,
            ],
            "taxonomy.": [
                EventAuditType.taxonomy_created,
                EventAuditType.taxonomy_updated,
                EventAuditType.taxonomy_deleted,
            ],
            "taxonomy.usage.": [
                EventAuditType.taxonomy_usage_updated,
                EventAuditType.taxonomy_usage_deleted,
            ],
            "taxonomy.element.": [
                EventAuditType.taxonomy_element_created,
                EventAuditType.taxonomy_element_updated,
                EventAuditType.taxonomy_element_deleted,
            ],
            "connection.": [
                EventAuditType.connection_created,
                EventAuditType.connection_updated,
                EventAuditType.connection_deleted,
            ],
            "connection.secrets.": [
                EventAuditType.connection_secrets_created,
                EventAuditType.connection_secrets_updated,
            ],
        }

        for prefix, expected_types in expected_patterns.items():
            for event_type in expected_types:
                assert event_type.value.startswith(
                    prefix
                ), f"{event_type.value} should start with {prefix}"

    def test_event_audit_types_are_strings(self):
        """Test that all EventAuditType values are strings."""
        for event_type in EventAuditType:
            assert isinstance(event_type.value, str)
            assert len(event_type.value) > 0

    def test_event_audit_types_unique(self):
        """Test that all EventAuditType values are unique."""
        values = [event_type.value for event_type in EventAuditType]
        assert len(values) == len(set(values)), "EventAuditType values should be unique"


class TestConnectionEventAuditTypes:
    """Tests specifically for connection-related event audit types."""

    def test_create_connection_audit_events(self, db, event_audit_service):
        """Test creating audit events for connection operations."""
        # Test connection created event
        connection_created_event = event_audit_service.create_event_audit(
            event_type=EventAuditType.connection_created,
            status=EventAuditStatus.succeeded,
            resource_type="connection_config",
            resource_identifier="postgres_db_1",
            description="Connection created: postgres connection 'postgres_db_1'",
            event_details={"operation_type": "created", "connection_type": "postgres"},
        )

        assert (
            connection_created_event.event_type
            == EventAuditType.connection_created.value
        )
        assert connection_created_event.resource_type == "connection_config"
        assert connection_created_event.resource_identifier == "postgres_db_1"
        assert "postgres connection" in connection_created_event.description
        assert connection_created_event.event_details["operation_type"] == "created"

        # Test connection updated event
        connection_updated_event = event_audit_service.create_event_audit(
            event_type=EventAuditType.connection_updated,
            status=EventAuditStatus.succeeded,
            resource_type="connection_config",
            resource_identifier="mysql_db_1",
            description="Connection updated: mysql connection 'mysql_db_1'",
            event_details={"operation_type": "updated", "connection_type": "mysql"},
        )

        assert (
            connection_updated_event.event_type
            == EventAuditType.connection_updated.value
        )
        assert connection_updated_event.resource_identifier == "mysql_db_1"

        # Test connection deleted event
        connection_deleted_event = event_audit_service.create_event_audit(
            event_type=EventAuditType.connection_deleted,
            status=EventAuditStatus.succeeded,
            resource_type="connection_config",
            resource_identifier="redis_cache_1",
            description="Connection deleted: redis connection 'redis_cache_1'",
            event_details={"operation_type": "deleted", "connection_type": "redis"},
        )

        assert (
            connection_deleted_event.event_type
            == EventAuditType.connection_deleted.value
        )
        assert connection_deleted_event.resource_identifier == "redis_cache_1"

    def test_create_connection_secrets_audit_events(self, db, event_audit_service):
        """Test creating audit events for connection secrets operations."""
        # Test connection secrets created event
        secrets_created_event = event_audit_service.create_event_audit(
            event_type=EventAuditType.connection_secrets_created,
            status=EventAuditStatus.succeeded,
            resource_type="connection_config",
            resource_identifier="mailchimp_connector",
            description="Connection secrets created: mailchimp connector 'mailchimp_connector' - api_key, server",
            event_details={
                "secrets": {"api_key": "**********", "server": "us1"},
                "saas_connector_type": "mailchimp",
            },
        )

        assert (
            secrets_created_event.event_type
            == EventAuditType.connection_secrets_created.value
        )
        assert secrets_created_event.resource_identifier == "mailchimp_connector"
        assert "mailchimp connector" in secrets_created_event.description
        assert secrets_created_event.event_details["secrets"]["api_key"] == "**********"
        assert secrets_created_event.event_details["saas_connector_type"] == "mailchimp"

        # Test connection secrets updated event
        secrets_updated_event = event_audit_service.create_event_audit(
            event_type=EventAuditType.connection_secrets_updated,
            status=EventAuditStatus.succeeded,
            resource_type="connection_config",
            resource_identifier="postgres_db_2",
            description="Connection secrets updated: postgres connection 'postgres_db_2' - password",
            event_details={
                "secrets": {"password": "**********", "username": "postgres_user"}
            },
        )

        assert (
            secrets_updated_event.event_type
            == EventAuditType.connection_secrets_updated.value
        )
        assert secrets_updated_event.resource_identifier == "postgres_db_2"
        assert "postgres connection" in secrets_updated_event.description
        assert (
            secrets_updated_event.event_details["secrets"]["password"] == "**********"
        )


class TestEventAuditServiceEdgeCases:
    """Tests for edge cases and error handling in EventAuditService."""

    def test_create_event_audit_with_none_event_details(self, db, event_audit_service):
        """Test creating event audit with None event_details."""
        event_audit = event_audit_service.create_event_audit(
            event_type=EventAuditType.system_updated,
            status=EventAuditStatus.succeeded,
            event_details=None,
        )

        assert event_audit.event_details is None

    def test_create_event_audit_with_empty_event_details(self, db, event_audit_service):
        """Test creating event audit with empty event_details dictionary."""
        event_audit = event_audit_service.create_event_audit(
            event_type=EventAuditType.system_updated,
            status=EventAuditStatus.succeeded,
            event_details={},
        )

        assert event_audit.event_details == {}

    def test_create_event_audit_with_very_long_description(
        self, db, event_audit_service
    ):
        """Test creating event audit with very long description."""
        long_description = "A" * 10000  # Very long string

        event_audit = event_audit_service.create_event_audit(
            event_type=EventAuditType.taxonomy_element_created,
            status=EventAuditStatus.succeeded,
            description=long_description,
        )

        assert event_audit.description == long_description

    def test_get_events_with_zero_limit(self, db, event_audit_service):
        """Test query methods with zero limit."""
        event_audit_service.create_event_audit(
            event_type=EventAuditType.system_updated,
            status=EventAuditStatus.succeeded,
        )

        events = event_audit_service.get_events_by_type(
            EventAuditType.system_updated, limit=0
        )
        assert len(events) == 0

    def test_create_event_audit_with_special_characters_in_strings(
        self, event_audit_service
    ):
        """Test creating event audit with special characters in string fields."""
        special_chars_data = {
            "unicode": "測試 🚀 ñoño",
            "symbols": "!@#$%^&*()_+-={}[]|\\:;\"'<>?,./",
        }

        event_audit = event_audit_service.create_event_audit(
            event_type=EventAuditType.taxonomy_updated,
            status=EventAuditStatus.succeeded,
            resource_identifier="special_chars_🔥",
            description="Testing special chars: 測試",
            event_details=special_chars_data,
        )

        assert event_audit.resource_identifier == "special_chars_🔥"
        assert event_audit.description == "Testing special chars: 測試"
        assert event_audit.event_details == special_chars_data
