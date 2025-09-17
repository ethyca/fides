import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.digest import DigestConfig, DigestType
from fides.api.schemas.messaging.messaging import MessagingMethod


class TestDigestConfigCreation:
    """Tests for creating and managing digest configurations."""

    def test_create_basic_digest_config(self, db: Session):
        """Test creating a basic digest configuration."""
        config = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.MANUAL_TASKS,
                "name": "Test Manual Task Digest",
                "description": "A test digest for manual tasks",
                "enabled": True,
                "cron_expression": "0 9 * * 1",  # Every Monday at 9 AM
                "timezone": "US/Eastern",
            },
        )

        assert config.id is not None
        assert config.digest_type == DigestType.MANUAL_TASKS
        assert config.name == "Test Manual Task Digest"
        assert config.description == "A test digest for manual tasks"
        assert config.enabled is True
        assert config.cron_expression == "0 9 * * 1"
        assert config.timezone == "US/Eastern"
        assert config.messaging_service_type == MessagingMethod.EMAIL  # Default
        assert config.last_sent_at is None
        assert config.next_scheduled_at is None
        assert config.config_metadata == {}
        assert config.created_at is not None
        assert config.updated_at is not None

    def test_create_privacy_request_digest(self, db: Session):
        """Test creating a privacy request digest configuration."""
        config = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.PRIVACY_REQUESTS,
                "name": "EU Privacy Request Digest",
                "description": "Weekly digest for EU privacy requests",
                "enabled": True,
                "messaging_service_type": MessagingMethod.EMAIL,
                "cron_expression": "0 10 * * 2",  # Every Tuesday at 10 AM
                "timezone": "Europe/London",
                "config_metadata": {
                    "region": "EU",
                    "export_format": "csv",
                    "include_attachments": True,
                },
            },
        )

        assert config.digest_type == DigestType.PRIVACY_REQUESTS
        assert config.name == "EU Privacy Request Digest"
        assert config.timezone == "Europe/London"
        assert config.config_metadata["region"] == "EU"
        assert config.config_metadata["export_format"] == "csv"
        assert config.config_metadata["include_attachments"] is True

    def test_create_minimal_digest_config(self, db: Session):
        """Test creating a digest config with only required fields."""
        config = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.MANUAL_TASKS,
                "name": "Minimal Digest",
            },
        )

        assert config.digest_type == DigestType.MANUAL_TASKS
        assert config.name == "Minimal Digest"
        assert config.description is None
        assert config.enabled is True  # Default
        assert config.messaging_service_type == MessagingMethod.EMAIL  # Default
        assert config.cron_expression is None
        assert config.timezone == "US/Eastern"  # Default
        assert config.config_metadata == {}

    def test_digest_config_defaults(self, db: Session):
        """Test that default values are properly set."""
        config = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.MANUAL_TASKS,
                "name": "Test Defaults",
            },
        )

        assert config.enabled is True
        assert config.messaging_service_type == MessagingMethod.EMAIL
        assert config.timezone == "US/Eastern"
        assert config.config_metadata == {}

    def test_name_is_required(self, db: Session):
        """Test that name field is required."""
        with pytest.raises(IntegrityError):
            DigestConfig.create(
                db=db,
                data={
                    "digest_type": DigestType.MANUAL_TASKS,
                    # Missing name
                },
            )

    def test_digest_type_is_required(self, db: Session):
        """Test that digest_type field is required."""
        with pytest.raises(IntegrityError):
            DigestConfig.create(
                db=db,
                data={
                    "name": "Test Config",
                    # Missing digest_type
                },
            )


class TestDigestConfigQueries:
    """Tests for querying digest configurations."""

    @pytest.fixture
    def sample_configs(self, db: Session):
        """Create sample digest configurations for testing."""
        configs = []

        # Manual task digest - enabled
        config1 = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.MANUAL_TASKS,
                "name": "US Manual Task Digest",
                "enabled": True,
                "cron_expression": "0 9 * * 1",
                "timezone": "US/Eastern",
                "config_metadata": {"region": "US"},
            },
        )
        configs.append(config1)

        # Privacy request digest - enabled
        config2 = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.PRIVACY_REQUESTS,
                "name": "EU Privacy Request Digest",
                "enabled": True,
                "cron_expression": "0 10 * * 2",
                "timezone": "Europe/London",
                "config_metadata": {"region": "EU"},
            },
        )
        configs.append(config2)

        # Manual task digest - disabled
        config3 = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.MANUAL_TASKS,
                "name": "Disabled Manual Task Digest",
                "enabled": False,
                "cron_expression": "0 8 * * *",
                "timezone": "Asia/Tokyo",
                "config_metadata": {"region": "APAC"},
            },
        )
        configs.append(config3)

        return configs

    def test_get_by_digest_type(self, db: Session, sample_configs):
        """Test filtering digest configs by type."""
        manual_task_configs = (
            db.query(DigestConfig)
            .filter(DigestConfig.digest_type == DigestType.MANUAL_TASKS)
            .all()
        )

        assert len(manual_task_configs) == 2
        assert all(
            config.digest_type == DigestType.MANUAL_TASKS
            for config in manual_task_configs
        )

    def test_get_enabled_configs(self, db: Session, sample_configs):
        """Test filtering digest configs by enabled status."""
        enabled_configs = (
            db.query(DigestConfig).filter(DigestConfig.enabled == True).all()
        )

        assert len(enabled_configs) == 2
        assert all(config.enabled is True for config in enabled_configs)

    def test_get_by_messaging_service_type(self, db: Session, sample_configs):
        """Test filtering digest configs by messaging service type."""
        email_configs = (
            db.query(DigestConfig)
            .filter(DigestConfig.messaging_service_type == MessagingMethod.EMAIL)
            .all()
        )

        assert len(email_configs) == 3  # All configs use email by default

    def test_get_configs_with_cron_expression(self, db: Session, sample_configs):
        """Test filtering digest configs that have cron expressions."""
        scheduled_configs = (
            db.query(DigestConfig)
            .filter(DigestConfig.cron_expression.isnot(None))
            .all()
        )

        assert len(scheduled_configs) == 3
        assert all(config.cron_expression is not None for config in scheduled_configs)


class TestDigestConfigUpdate:
    """Tests for updating digest configurations."""

    @pytest.fixture
    def digest_config(self, db: Session):
        """Create a test digest configuration."""
        return DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.MANUAL_TASKS,
                "name": "Test Digest",
                "description": "Original description",
                "enabled": True,
                "cron_expression": "0 9 * * 1",
                "timezone": "US/Eastern",
                "config_metadata": {"version": 1},
            },
        )

    def test_update_basic_fields(self, db: Session, digest_config):
        """Test updating basic digest configuration fields."""
        original_updated_at = digest_config.updated_at

        digest_config.name = "Updated Digest Name"
        digest_config.description = "Updated description"
        digest_config.enabled = False
        digest_config.save(db)

        # Refresh from database
        db.refresh(digest_config)

        assert digest_config.name == "Updated Digest Name"
        assert digest_config.description == "Updated description"
        assert digest_config.enabled is False
        assert digest_config.updated_at > original_updated_at

    def test_update_scheduling_fields(self, db: Session, digest_config):
        """Test updating scheduling-related fields."""
        digest_config.cron_expression = "0 8 * * 2"  # Tuesday at 8 AM
        digest_config.timezone = "Europe/London"
        digest_config.save(db)

        db.refresh(digest_config)

        assert digest_config.cron_expression == "0 8 * * 2"
        assert digest_config.timezone == "Europe/London"

    def test_update_metadata(self, db: Session, digest_config):
        """Test updating metadata field."""
        new_metadata = {
            "version": 2,
            "region": "US",
            "max_items": 50,
            "features": ["priority_sorting", "attachments"],
        }

        digest_config.config_metadata = new_metadata
        digest_config.save(db)

        db.refresh(digest_config)

        assert digest_config.config_metadata == new_metadata
        assert digest_config.config_metadata["version"] == 2
        assert digest_config.config_metadata["region"] == "US"
        assert digest_config.config_metadata["max_items"] == 50
        assert "priority_sorting" in digest_config.config_metadata["features"]


class TestDigestConfigDeletion:
    """Tests for deleting digest configurations."""

    def test_delete_digest_config(self, db: Session):
        """Test deleting a digest configuration."""
        config = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.MANUAL_TASKS,
                "name": "To Be Deleted",
            },
        )

        config_id = config.id
        config.delete(db)

        # Verify it's deleted
        deleted_config = (
            db.query(DigestConfig).filter(DigestConfig.id == config_id).first()
        )
        assert deleted_config is None

    def test_delete_nonexistent_config(self, db: Session):
        """Test deleting a config that doesn't exist doesn't raise error."""
        config = DigestConfig(
            id="nonexistent_id",
            digest_type=DigestType.MANUAL_TASKS,
            name="Nonexistent",
        )

        # Should not raise an error
        config.delete(db)


class TestDigestConfigConditionMethods:
    """Tests for digest configuration condition methods."""

    @pytest.fixture
    def digest_config(self, db: Session):
        """Create a test digest configuration."""
        return DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.MANUAL_TASKS,
                "name": "Test Conditions Digest",
            },
        )

    def test_get_receiver_conditions_not_implemented(self, db: Session, digest_config):
        """Test that receiver conditions method raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Conditions are not implemented for digests"
        ):
            digest_config.get_receiver_conditions(db)

    def test_get_content_conditions_not_implemented(self, db: Session, digest_config):
        """Test that content conditions method raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Conditions are not implemented for digests"
        ):
            digest_config.get_content_conditions(db)

    def test_get_priority_conditions_not_implemented(self, db: Session, digest_config):
        """Test that priority conditions method raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Conditions are not implemented for digests"
        ):
            digest_config.get_priority_conditions(db)

    def test_get_all_conditions_not_implemented(self, db: Session, digest_config):
        """Test that all conditions method raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match="Conditions are not implemented for digests"
        ):
            digest_config.get_all_conditions(db)


class TestDigestConfigValidation:
    """Tests for digest configuration validation and constraints."""

    def test_valid_digest_types(self, db: Session):
        """Test that all valid digest types can be created."""
        for digest_type in DigestType:
            config = DigestConfig.create(
                db=db,
                data={
                    "digest_type": digest_type,
                    "name": f"Test {digest_type.value} Digest",
                },
            )
            assert config.digest_type == digest_type
            config.delete(db)  # Clean up

    def test_valid_messaging_service_types(self, db: Session):
        """Test that valid messaging service types can be set."""
        config = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.MANUAL_TASKS,
                "name": "Test Messaging Types",
                "messaging_service_type": MessagingMethod.EMAIL,
            },
        )
        assert config.messaging_service_type == MessagingMethod.EMAIL

    def test_complex_metadata_structure(self, db: Session):
        """Test that complex metadata structures are properly stored."""
        complex_metadata = {
            "regions": ["US", "EU", "APAC"],
            "settings": {
                "max_items": 100,
                "include_attachments": True,
                "priority_threshold": "high",
                "filters": {
                    "status": ["pending", "in_progress"],
                    "age_days": {"min": 0, "max": 30},
                },
            },
            "templates": {
                "subject": "Weekly Digest - {count} items",
                "header": "Your weekly summary",
            },
            "recipients": {
                "roles": ["admin", "manager"],
                "departments": ["legal", "compliance"],
            },
        }

        config = DigestConfig.create(
            db=db,
            data={
                "digest_type": DigestType.PRIVACY_REQUESTS,
                "name": "Complex Metadata Test",
                "config_metadata": complex_metadata,
            },
        )

        db.refresh(config)

        assert config.config_metadata == complex_metadata
        assert config.config_metadata["regions"] == ["US", "EU", "APAC"]
        assert config.config_metadata["settings"]["max_items"] == 100
        assert config.config_metadata["settings"]["filters"]["status"] == [
            "pending",
            "in_progress",
        ]
        assert (
            config.config_metadata["templates"]["subject"]
            == "Weekly Digest - {count} items"
        )
