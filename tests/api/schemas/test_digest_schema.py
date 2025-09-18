import json

import pytest
from pydantic import ValidationError

from fides.api.models.digest.digest_config import DigestType
from fides.api.schemas.digest import DigestConfigBase
from fides.api.schemas.messaging.messaging import MessagingMethod


class TestDigestConfigBase:
    """Test the DigestConfigBase schema validation."""

    def test_valid_minimal_config(self):
        """Test creating a valid minimal digest configuration."""
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
        )

        assert config.digest_type == DigestType.MANUAL_TASKS
        assert config.name == "Test Digest"
        assert config.description is None
        assert config.enabled is True  # Default
        assert config.messaging_service_type == MessagingMethod.EMAIL  # Default
        assert config.cron_expression is None
        assert config.timezone == "US/Eastern"  # Default
        assert config.config_metadata == {}  # Default

    def test_valid_full_config(self):
        """Test creating a valid full digest configuration."""
        config = DigestConfigBase(
            digest_type=DigestType.PRIVACY_REQUESTS,
            name="Privacy Request Weekly Digest",
            description="Weekly summary of privacy requests",
            enabled=False,
            messaging_service_type=MessagingMethod.EMAIL,
            cron_expression="0 10 * * 2",
            timezone="Europe/London",
            config_metadata={"version": 1, "template": "standard"},
        )

        assert config.digest_type == DigestType.PRIVACY_REQUESTS
        assert config.name == "Privacy Request Weekly Digest"
        assert config.description == "Weekly summary of privacy requests"
        assert config.enabled is False
        assert config.messaging_service_type == MessagingMethod.EMAIL
        assert config.cron_expression == "0 10 * * 2"
        assert config.timezone == "Europe/London"
        assert config.config_metadata == {"version": 1, "template": "standard"}

    def test_all_digest_types(self):
        """Test all supported digest types."""
        for digest_type in DigestType:
            config = DigestConfigBase(
                digest_type=digest_type,
                name=f"Test {digest_type.value} Digest",
            )
            assert config.digest_type == digest_type

    def test_all_messaging_methods(self):
        """Test all supported messaging service types."""
        for messaging_method in MessagingMethod:
            config = DigestConfigBase(
                digest_type=DigestType.MANUAL_TASKS,
                name="Test Digest",
                messaging_service_type=messaging_method,
            )
            assert config.messaging_service_type == messaging_method


class TestDigestConfigValidation:
    """Test validation rules for DigestConfigBase."""

    def test_name_required(self):
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            DigestConfigBase(
                digest_type=DigestType.MANUAL_TASKS,
                # name is missing
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("name",)

    def test_digest_type_required(self):
        """Test that digest_type is required."""
        with pytest.raises(ValidationError) as exc_info:
            DigestConfigBase(
                name="Test Digest",
                # digest_type is missing
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("digest_type",)

    def test_name_length_validation(self):
        """Test name length constraints."""
        # Test empty string
        with pytest.raises(ValidationError) as exc_info:
            DigestConfigBase(
                digest_type=DigestType.MANUAL_TASKS,
                name="",
            )

        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_short" for error in errors)

        # Test maximum length (255 characters)
        long_name = "a" * 256
        with pytest.raises(ValidationError) as exc_info:
            DigestConfigBase(
                digest_type=DigestType.MANUAL_TASKS,
                name=long_name,
            )

        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_long" for error in errors)

        # Test valid length
        valid_name = "a" * 255
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name=valid_name,
        )
        assert config.name == valid_name

    def test_description_length_validation(self):
        """Test description length constraints."""
        # Test maximum length (1000 characters)
        long_description = "a" * 1001
        with pytest.raises(ValidationError) as exc_info:
            DigestConfigBase(
                digest_type=DigestType.MANUAL_TASKS,
                name="Test Digest",
                description=long_description,
            )

        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_long" for error in errors)

        # Test valid length
        valid_description = "a" * 1000
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
            description=valid_description,
        )
        assert config.description == valid_description

    def test_extra_fields_forbidden(self):
        """Test that extra fields are not allowed."""
        with pytest.raises(ValidationError) as exc_info:
            DigestConfigBase(
                digest_type=DigestType.MANUAL_TASKS,
                name="Test Digest",
                extra_field="not allowed",
            )

        errors = exc_info.value.errors()
        assert any(error["type"] == "extra_forbidden" for error in errors)


class TestCronExpressionValidation:
    """Test cron expression validation."""

    @pytest.mark.parametrize(
        "valid_cron",
        [
            "0 9 * * 1",  # Every Monday at 9 AM
            "0 10 * * 2",  # Every Tuesday at 10 AM
            "*/15 * * * *",  # Every 15 minutes
            "0 0 1 * *",  # First day of every month at midnight
            "0 8-17 * * 1-5",  # Every hour from 8-17 on weekdays
            "0 9 * * MON",  # Every Monday at 9 AM (with name)
            "0 0 0 * * *",  # 6-field cron expression (with seconds)
        ],
    )
    def test_valid_cron_expressions(self, valid_cron):
        """Test valid cron expressions."""
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
            cron_expression=valid_cron,
        )
        assert config.cron_expression == valid_cron

    def test_none_cron_expression(self):
        """Test that None is allowed for cron expression."""
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
            cron_expression=None,
        )
        assert config.cron_expression is None

    @pytest.mark.parametrize(
        "invalid_cron,expected_error",
        [
            ("", "Cron expression must have 5 or 6 fields"),
            ("0", "Cron expression must have 5 or 6 fields"),
            ("0 9", "Cron expression must have 5 or 6 fields"),
            ("0 9 *", "Cron expression must have 5 or 6 fields"),
            ("0 9 * *", "Cron expression must have 5 or 6 fields"),
            ("0 9 * * * * *", "Cron expression must have 5 or 6 fields"),
            ("   ", "Cron expression must have 5 or 6 fields"),
        ],
    )
    def test_invalid_cron_expressions(self, invalid_cron, expected_error):
        """Test invalid cron expressions."""
        with pytest.raises(ValidationError) as exc_info:
            DigestConfigBase(
                digest_type=DigestType.MANUAL_TASKS,
                name="Test Digest",
                cron_expression=invalid_cron,
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert expected_error in str(errors[0]["ctx"]["error"])

    def test_cron_expression_max_length(self):
        """Test cron expression maximum length validation."""
        long_cron = "a" * 101
        with pytest.raises(ValidationError) as exc_info:
            DigestConfigBase(
                digest_type=DigestType.MANUAL_TASKS,
                name="Test Digest",
                cron_expression=long_cron,
            )

        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_long" for error in errors)


class TestTimezoneValidation:
    """Test timezone validation."""

    @pytest.mark.parametrize(
        "valid_timezone",
        [
            "US/Eastern",
            "US/Pacific",
            "Europe/London",
            "Europe/Paris",
            "Asia/Tokyo",
            "UTC",
            "America/New_York",
            "America/Los_Angeles",
            "Australia/Sydney",
        ],
    )
    def test_valid_timezones(self, valid_timezone):
        """Test valid timezone strings."""
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
            timezone=valid_timezone,
        )
        assert config.timezone == valid_timezone

    @pytest.mark.parametrize(
        "invalid_timezone",
        [
            "Invalid/Timezone",
            "Not/A/Real/Zone",
            "PST",  # Deprecated abbreviation
            "US/Invalid",
            "Europe/Invalid",
        ],
    )
    def test_invalid_timezones(self, invalid_timezone):
        """Test invalid timezone strings."""
        with pytest.raises(ValidationError) as exc_info:
            DigestConfigBase(
                digest_type=DigestType.MANUAL_TASKS,
                name="Test Digest",
                timezone=invalid_timezone,
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        # The error message can vary depending on the invalid timezone format
        error_msg = str(errors[0]["ctx"]["error"])
        assert any(
            phrase in error_msg
            for phrase in ["Invalid timezone", "ZoneInfo keys", "does not exist"]
        )

    def test_empty_timezone_string(self):
        """Test empty timezone string specifically."""
        with pytest.raises(ValidationError) as exc_info:
            DigestConfigBase(
                digest_type=DigestType.MANUAL_TASKS,
                name="Test Digest",
                timezone="",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        # Empty string produces a specific error message
        error_msg = str(errors[0]["ctx"]["error"])
        assert "ZoneInfo keys must be normalized relative paths" in error_msg

    def test_timezone_max_length(self):
        """Test timezone maximum length validation."""
        long_timezone = "a" * 51
        with pytest.raises(ValidationError) as exc_info:
            DigestConfigBase(
                digest_type=DigestType.MANUAL_TASKS,
                name="Test Digest",
                timezone=long_timezone,
            )

        errors = exc_info.value.errors()
        assert any(error["type"] == "string_too_long" for error in errors)


class TestConfigMetadataValidation:
    """Test config metadata validation."""

    def test_simple_metadata(self):
        """Test simple metadata structures."""
        metadata = {"version": 1, "enabled": True}
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
            config_metadata=metadata,
        )
        assert config.config_metadata == metadata

    def test_nested_metadata(self):
        """Test nested metadata structures."""
        metadata = {
            "template": {
                "name": "standard",
                "version": "1.0",
                "settings": {
                    "include_summary": True,
                    "max_items": 100,
                },
            },
            "recipients": ["admin@example.com", "manager@example.com"],
        }
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
            config_metadata=metadata,
        )
        assert config.config_metadata == metadata

    def test_empty_metadata(self):
        """Test empty metadata."""
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
            config_metadata={},
        )
        assert config.config_metadata == {}

    def test_none_metadata(self):
        """Test None metadata (stays None when explicitly set)."""
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
            config_metadata=None,
        )
        assert config.config_metadata is None

    def test_metadata_with_various_types(self):
        """Test metadata with various data types."""
        metadata = {
            "string_field": "test",
            "int_field": 42,
            "float_field": 3.14,
            "bool_field": True,
            "list_field": [1, 2, 3],
            "null_field": None,
        }
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
            config_metadata=metadata,
        )
        assert config.config_metadata == metadata


class TestDigestConfigDefaults:
    """Test default values for DigestConfigBase."""

    def test_default_values(self):
        """Test that default values are applied correctly."""
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
        )

        # Test defaults
        assert config.enabled is True
        assert config.messaging_service_type == MessagingMethod.EMAIL
        assert config.timezone == "US/Eastern"
        assert config.config_metadata == {}

        # Test None defaults
        assert config.description is None
        assert config.cron_expression is None

    def test_explicit_values_override_defaults(self):
        """Test that explicitly provided values override defaults."""
        config = DigestConfigBase(
            digest_type=DigestType.PRIVACY_REQUESTS,
            name="Custom Digest",
            enabled=False,
            messaging_service_type=MessagingMethod.EMAIL,
            timezone="Europe/London",
            config_metadata={"custom": True},
        )

        assert config.enabled is False
        assert config.messaging_service_type == MessagingMethod.EMAIL
        assert config.timezone == "Europe/London"
        assert config.config_metadata == {"custom": True}


class TestDigestConfigSerialization:
    """Test serialization and deserialization of DigestConfigBase."""

    def test_model_dump(self):
        """Test converting model to dictionary."""
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
            description="Test description",
            enabled=True,
            messaging_service_type=MessagingMethod.EMAIL,
            cron_expression="0 9 * * 1",
            timezone="US/Eastern",
            config_metadata={"version": 1},
        )

        data = config.model_dump(mode="json")
        expected = {
            "digest_type": "manual_tasks",
            "name": "Test Digest",
            "description": "Test description",
            "enabled": True,
            "messaging_service_type": "email",
            "cron_expression": "0 9 * * 1",
            "timezone": "US/Eastern",
            "config_metadata": {"version": 1},
        }

        assert data == expected

    def test_model_dump_exclude_none(self):
        """Test excluding None values from serialization."""
        config = DigestConfigBase(
            digest_type=DigestType.MANUAL_TASKS,
            name="Test Digest",
            description=None,
            cron_expression=None,
        )

        data = config.model_dump(exclude_none=True)

        # None values should be excluded
        assert "description" not in data
        assert "cron_expression" not in data

        # Other values should be present
        assert data["digest_type"] == "manual_tasks"
        assert data["name"] == "Test Digest"
        assert data["enabled"] is True

    def test_json_serialization(self):
        """Test JSON serialization."""
        config = DigestConfigBase(
            digest_type=DigestType.PRIVACY_REQUESTS,
            name="JSON Test Digest",
            config_metadata={"nested": {"value": 42}},
        )

        json_str = config.model_dump_json()
        assert isinstance(json_str, str)

        parsed = json.loads(json_str)
        assert parsed["digest_type"] == "privacy_requests"
        assert parsed["name"] == "JSON Test Digest"
        assert parsed["config_metadata"]["nested"]["value"] == 42
