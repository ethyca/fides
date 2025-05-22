import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.detection_discovery import MonitorConfig, SharedMonitorConfig


@pytest.fixture(scope="function")
def shared_monitor_config(db: Session) -> SharedMonitorConfig:
    """Fixture for creating a test SharedMonitorConfig"""
    shared_config = SharedMonitorConfig.create(
        db=db,
        data={
            "name": "test shared config",
            "key": "test_shared_config",
            "description": "Test shared monitor configuration",
            "classify_params": {
                "context_regex_pattern_mapping": [
                    [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
                    [".*[P|p]hone_number.*", "user.contact.phone_number"],
                ]
            },
        },
    )
    yield shared_config
    try:
        db.delete(shared_config)
    except ObjectDeletedError:
        # Object was already deleted, do nothing
        return


class TestSharedMonitorConfigModel:
    def test_create_shared_monitor_config(
        self, db: Session, shared_monitor_config
    ) -> None:
        """
        Tests that a SharedMonitorConfig can be created successfully
        and that we can access its attributes as expected.
        """
        config = SharedMonitorConfig.get(db=db, object_id=shared_monitor_config.id)
        assert config.name == "test shared config"
        assert config.key == "test_shared_config"
        assert config.description == "Test shared monitor configuration"
        assert config.classify_params == {
            "context_regex_pattern_mapping": [
                [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
                [".*[P|p]hone_number.*", "user.contact.phone_number"],
            ]
        }

    def test_update_shared_monitor_config(
        self, db: Session, shared_monitor_config
    ) -> None:
        """Tests that a SharedMonitorConfig can be updated successfully"""
        # Update the shared config
        shared_monitor_config.update(
            db=db,
            data={
                "name": "updated shared config",
                "description": "Updated description",
                "classify_params": {
                    "context_regex_pattern_mapping": [
                        [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
                        [".*[P|p]hone_number.*", "user.contact.phone_number"],
                        [".*[A|a]ddress.*", "user.contact.address"],
                    ]
                },
            },
        )

        # Retrieve the updated config from the DB and verify changes
        updated_config = SharedMonitorConfig.get(
            db=db, object_id=shared_monitor_config.id
        )
        assert updated_config.name == "updated shared config"
        assert updated_config.key == "test_shared_config"  # key should not change
        assert updated_config.description == "Updated description"
        assert updated_config.classify_params == {
            "context_regex_pattern_mapping": [
                [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
                [".*[P|p]hone_number.*", "user.contact.phone_number"],
                [".*[A|a]ddress.*", "user.contact.address"],
            ]
        }

    def test_get_shared_monitor_config_by_key(
        self, db: Session, shared_monitor_config
    ) -> None:
        """Tests that a SharedMonitorConfig can be retrieved by key"""
        # Get by key
        config = SharedMonitorConfig.get_by(
            db=db, field="key", value="test_shared_config"
        )
        assert config is not None
        assert config.id == shared_monitor_config.id
        assert config.name == "test shared config"
        # Check that the first entry in context_regex_pattern_mapping is for email
        assert (
            config.classify_params["context_regex_pattern_mapping"][0][1]
            == "user.contact.email"
        )

    def test_delete_shared_monitor_config(self, db: Session) -> None:
        """Tests that a SharedMonitorConfig can be deleted"""
        # Create a config to delete
        config_to_delete = SharedMonitorConfig.create(
            db=db,
            data={
                "name": "config to delete",
                "key": "config_to_delete",
                "description": "This config will be deleted",
                "classify_params": {
                    "context_regex_pattern_mapping": [[".*test.*", "system"]]
                },
            },
        )

        # Verify it was created
        config_id = config_to_delete.id
        assert SharedMonitorConfig.get(db=db, object_id=config_id) is not None

        # Delete it
        config_to_delete.delete(db=db)

        # Verify it was deleted
        assert SharedMonitorConfig.get(db=db, object_id=config_id) is None

    def test_delete_constraint_with_monitor_config(
        self, db: Session, shared_monitor_config, connection_config: ConnectionConfig
    ) -> None:
        """
        Test that a SharedMonitorConfig cannot be deleted if it is referenced by a MonitorConfig
        due to the RESTRICT constraint.
        """
        # Create a monitor config that references the shared config
        monitor_config = MonitorConfig.create(
            db=db,
            data={
                "name": "monitor with shared config reference",
                "key": "monitor_with_shared_config_ref",
                "connection_config_id": connection_config.id,
                "shared_config_id": shared_monitor_config.id,
            },
        )

        # Attempt to delete the shared config - should fail due to RESTRICT constraint
        with pytest.raises(IntegrityError):
            shared_monitor_config.delete(db=db)
            db.flush()  # Force the constraint check

        # Verify shared config still exists
        assert (
            SharedMonitorConfig.get(db=db, object_id=shared_monitor_config.id)
            is not None
        )

        # Now delete the monitor config first
        monitor_config.delete(db=db)

        # Now we should be able to delete the shared config
        shared_monitor_config.delete(db=db)

        # Verify shared config is now deleted
        assert (
            SharedMonitorConfig.get(db=db, object_id=shared_monitor_config.id) is None
        )

    def test_shared_config_updates_propagate(
        self, db: Session, shared_monitor_config, connection_config: ConnectionConfig
    ) -> None:
        """
        Test that when a SharedMonitorConfig is updated, all MonitorConfigs
        that reference it will get the updated values.
        """
        # Create two monitor configs that reference the same shared config
        monitor_config_1 = MonitorConfig.create(
            db=db,
            data={
                "name": "monitor config 1",
                "key": "monitor_config_1",
                "connection_config_id": connection_config.id,
                "shared_config_id": shared_monitor_config.id,
            },
        )

        monitor_config_2 = MonitorConfig.create(
            db=db,
            data={
                "name": "monitor config 2",
                "key": "monitor_config_2",
                "connection_config_id": connection_config.id,
                "shared_config_id": shared_monitor_config.id,
            },
        )

        # Initial values should match the shared config
        assert monitor_config_1.classify_params["context_regex_pattern_mapping"] == [
            [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
            [".*[P|p]hone_number.*", "user.contact.phone_number"],
        ]
        assert monitor_config_2.classify_params["context_regex_pattern_mapping"] == [
            [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
            [".*[P|p]hone_number.*", "user.contact.phone_number"],
        ]

        # Update the shared config
        shared_monitor_config.update(
            db=db,
            data={
                "classify_params": {
                    "context_regex_pattern_mapping": [
                        [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
                        [".*[P|p]hone_number.*", "user.contact.phone_number"],
                        [
                            ".*[S|s]sn.*",
                            "user.government_id.national_identification_number",
                        ],
                    ]
                },
            },
        )

        # Refresh the MonitorConfig objects from DB
        updated_monitor_config_1 = MonitorConfig.get(
            db=db, object_id=monitor_config_1.id
        )
        updated_monitor_config_2 = MonitorConfig.get(
            db=db, object_id=monitor_config_2.id
        )

        # Both should have the updated pattern mapping
        assert updated_monitor_config_1.classify_params[
            "context_regex_pattern_mapping"
        ] == [
            [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
            [".*[P|p]hone_number.*", "user.contact.phone_number"],
            [".*[S|s]sn.*", "user.government_id.national_identification_number"],
        ]
        assert updated_monitor_config_2.classify_params[
            "context_regex_pattern_mapping"
        ] == [
            [".*([e|E]mail|[e|E]mail_address).*", "user.contact.email"],
            [".*[P|p]hone_number.*", "user.contact.phone_number"],
            [".*[S|s]sn.*", "user.government_id.national_identification_number"],
        ]
