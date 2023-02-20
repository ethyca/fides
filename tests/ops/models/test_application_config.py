from json import dumps
from typing import Any, Dict

import pytest
from sqlalchemy.orm import Session

from fides.api.ops.models.application_config import ApplicationConfig, _get_property
from fides.core.config import get_config
from fides.core.config.config_proxy import ConfigProxy

CONFIG = get_config()


class TestApplicationConfigModel:
    @pytest.fixture(scope="function")
    def example_config_dict(self) -> Dict[str, str]:
        return {
            "setting1": "value1",
            "setting2": "value2",
            "setting3": {
                "nested_setting_1": "nested_value_1",
                "nested_setting_2": "nested_value_2",
            },
        }

    # TODO  - parameterize everything to test for `config_set` as well
    @pytest.fixture(scope="function")
    def example_config_record(self, example_config_dict) -> Dict[str, Any]:
        return {"api_set": example_config_dict}

    def test_create_or_update_keeps_single_record(
        self,
        db: Session,
        example_config_record: Dict[str, Any],
    ):
        """
        Ensure create_or_update properly restricts the table to a single record
        """
        config_record: ApplicationConfig = ApplicationConfig.create_or_update(
            db, data=example_config_record
        )
        assert config_record.api_set == example_config_record["api_set"]
        assert len(db.query(ApplicationConfig).all()) == 1
        config_record_db = db.query(ApplicationConfig).first()
        assert config_record_db.api_set == example_config_record["api_set"]
        assert config_record_db.id == config_record.id

        # make an arbitrary change to settings dict
        # and assert create_or_update just updated the same single record
        example_config_record["api_set"]["setting4"] = "value4"
        new_config_record: ApplicationConfig = ApplicationConfig.create_or_update(
            db, data=example_config_record
        )
        assert new_config_record.api_set == example_config_record["api_set"]
        assert new_config_record.id == config_record.id
        assert len(db.query(ApplicationConfig).all()) == 1
        new_config_record_db = db.query(ApplicationConfig).first()
        assert new_config_record_db.api_set == example_config_record["api_set"]
        assert new_config_record_db.id == new_config_record.id

    def test_create_or_update_merges_settings_dict(
        self,
        db: Session,
        example_config_record: Dict[str, Any],
    ):
        config_record: ApplicationConfig = ApplicationConfig.create_or_update(
            db, data=example_config_record
        )
        assert config_record.api_set == example_config_record["api_set"]
        assert len(db.query(ApplicationConfig).all()) == 1
        config_record_db = db.query(ApplicationConfig).first()
        assert config_record_db.api_set == example_config_record["api_set"]
        assert config_record_db.id == config_record.id

        # update one setting only
        new_config_record = {"api_set": {"setting1": "new_value"}}
        config_record: ApplicationConfig = ApplicationConfig.create_or_update(
            db, data=new_config_record
        )
        assert config_record.api_set["setting1"] == "new_value"
        assert config_record.api_set["setting2"] == "value2"
        assert len(db.query(ApplicationConfig).all()) == 1
        config_record_db = db.query(ApplicationConfig).first()
        assert config_record_db.api_set["setting1"] == "new_value"
        assert config_record_db.api_set["setting2"] == "value2"
        assert config_record_db.id == config_record.id

    def test_create_or_update_can_remove_entry(
        self,
        db: Session,
        example_config_record: Dict[str, Any],
    ):
        config_record: ApplicationConfig = ApplicationConfig.create_or_update(
            db, data=example_config_record
        )
        assert config_record.api_set == example_config_record["api_set"]
        assert len(db.query(ApplicationConfig).all()) == 1
        config_record_db = db.query(ApplicationConfig).first()
        assert config_record_db.api_set == example_config_record["api_set"]
        assert config_record_db.id == config_record.id

        # remove a setting by setting it to `None`
        new_config_record = {"api_set": {"setting1": None}}
        config_record: ApplicationConfig = ApplicationConfig.create_or_update(
            db, data=new_config_record
        )
        assert config_record.api_set["setting1"] is None
        assert config_record.api_set["setting2"] == "value2"
        assert len(db.query(ApplicationConfig).all()) == 1
        config_record_db = db.query(ApplicationConfig).first()
        assert config_record_db.api_set["setting1"] is None
        assert config_record_db.api_set["setting2"] == "value2"
        assert config_record_db.id == config_record.id

    def test_create_or_update_merges_nested_properties(
        self,
        db: Session,
        example_config_record: Dict[str, Any],
    ):
        config_record: ApplicationConfig = ApplicationConfig.create_or_update(
            db, data=example_config_record
        )
        assert config_record.api_set == example_config_record["api_set"]
        assert len(db.query(ApplicationConfig).all()) == 1
        config_record_db = db.query(ApplicationConfig).first()
        assert config_record_db.api_set == example_config_record["api_set"]
        assert config_record_db.id == config_record.id

        # update a single nested property
        new_config_record = {
            "api_set": {"setting3": {"nested_setting_1": "new_nested_value_1"}}
        }
        config_record: ApplicationConfig = ApplicationConfig.create_or_update(
            db, data=new_config_record
        )
        assert config_record.api_set["setting1"] == "value1"
        assert config_record.api_set["setting2"] == "value2"
        assert (
            config_record.api_set["setting3"]["nested_setting_1"]
            == "new_nested_value_1"
        )
        assert config_record.api_set["setting3"]["nested_setting_2"] == "nested_value_2"
        assert len(db.query(ApplicationConfig).all()) == 1
        config_record_db = db.query(ApplicationConfig).first()
        assert config_record_db.api_set["setting1"] == "value1"
        assert config_record_db.api_set["setting2"] == "value2"
        assert (
            config_record_db.api_set["setting3"]["nested_setting_1"]
            == "new_nested_value_1"
        )
        assert (
            config_record_db.api_set["setting3"]["nested_setting_2"] == "nested_value_2"
        )
        assert config_record_db.id == config_record.id

        # add a nested property
        new_config_record = {
            "api_set": {"setting3": {"nested_setting_3": "nested_value_3"}}
        }
        config_record: ApplicationConfig = ApplicationConfig.create_or_update(
            db, data=new_config_record
        )
        assert config_record.api_set["setting1"] == "value1"
        assert config_record.api_set["setting2"] == "value2"
        assert (
            config_record.api_set["setting3"]["nested_setting_1"]
            == "new_nested_value_1"
        )
        assert config_record.api_set["setting3"]["nested_setting_2"] == "nested_value_2"
        assert config_record.api_set["setting3"]["nested_setting_3"] == "nested_value_3"
        assert len(db.query(ApplicationConfig).all()) == 1
        config_record_db = db.query(ApplicationConfig).first()
        assert config_record_db.api_set["setting1"] == "value1"
        assert config_record_db.api_set["setting2"] == "value2"
        assert (
            config_record_db.api_set["setting3"]["nested_setting_1"]
            == "new_nested_value_1"
        )
        assert (
            config_record_db.api_set["setting3"]["nested_setting_2"] == "nested_value_2"
        )
        assert (
            config_record_db.api_set["setting3"]["nested_setting_3"] == "nested_value_3"
        )
        assert config_record_db.id == config_record.id

        # change a nested property to non-nested
        new_config_record = {"api_set": {"setting3": "value3"}}
        config_record: ApplicationConfig = ApplicationConfig.create_or_update(
            db, data=new_config_record
        )
        assert config_record.api_set["setting1"] == "value1"
        assert config_record.api_set["setting2"] == "value2"
        assert config_record.api_set["setting3"] == "value3"
        assert len(db.query(ApplicationConfig).all()) == 1
        config_record_db = db.query(ApplicationConfig).first()
        assert config_record_db.api_set["setting1"] == "value1"
        assert config_record_db.api_set["setting2"] == "value2"
        assert config_record.api_set["setting3"] == "value3"
        assert config_record_db.id == config_record.id

    def test_get_api_config_nothing_set(
        self,
        db: Session,
    ):
        assert ApplicationConfig.get_api_set(db) == {}

    def test_get_api_config(self, db: Session, example_config_record: Dict[str, Any]):
        ApplicationConfig.create_or_update(db, data=example_config_record)
        assert ApplicationConfig.get_api_set(db) == example_config_record["api_set"]

    def test_update_config_set(self, db):
        ApplicationConfig.update_config_set(db, CONFIG)
        # check a few specific config properties of different types on the database record
        db_config = ApplicationConfig.get_config_set(db)
        assert dumps(db_config) == CONFIG.json()

        # change a few config values, set the db record, ensure it's updated
        notification_service_type = CONFIG.notifications.notification_service_type
        execution_strict = CONFIG.execution.masking_strict
        CONFIG.notifications.notification_service_type = (
            notification_service_type + "_changed"
        )
        CONFIG.execution.masking_strict = (
            not execution_strict
        )  # since it's a boolean, switch the value

        # these shouldn't be equal before we update the db record
        assert (
            db_config["notifications"]["notification_service_type"]
            != CONFIG.notifications.notification_service_type
        )
        assert (
            db_config["execution"]["masking_strict"] != CONFIG.execution.masking_strict
        )
        # now we update the db record and all values should align again
        ApplicationConfig.update_config_set(db, CONFIG)
        db_config = ApplicationConfig.get_config_set(db)
        assert dumps(db_config) == CONFIG.json()

        # reset config values to initial values to ensure we don't mess up any state
        CONFIG.notifications.notification_service_type = notification_service_type
        CONFIG.execution.masking_strict = execution_strict


class TestApplicationConfigResolution:
    @pytest.mark.parametrize(
        "prop_dict, prop_path, expected_value",
        [
            ({}, "spam", None),
            ({"spam": "ham"}, "eggs", None),
            ({"spam": "ham"}, "spam", "ham"),
            ({"spam": "ham", "eggs": "overeasy"}, "spam", "ham"),
            ({"spam": "ham", "eggs": "overeasy"}, "eggs", "overeasy"),
            ({"spam": 1}, "spam", 1),
            ({"spam": False}, "spam", False),
            ({"spam": ["ham", "eggs"]}, "spam", ["ham", "eggs"]),
            ({"spam": "ham"}, "spam.", "ham"),
            ({"spam": {"spam1": "ham1"}}, "spam", {"spam1": "ham1"}),
            ({"spam": {"spam1": "ham1"}}, "spam.spam1", "ham1"),
            ({"spam": {"spam1": "ham1"}, "eggs": "overeasy"}, "spam.spam1", "ham1"),
            ({"spam": {"spam1": "ham1"}, "eggs": "overeasy"}, "spam.spam1.", "ham1"),
            (
                {"spam": {"spam1": {"spam2": "ham2"}}, "eggs": "overeasy"},
                "spam.spam1.spam2",
                "ham2",
            ),
            (
                {"spam": {"spam1": {"spam2": "ham2"}}, "eggs": "overeasy"},
                "spam.spam1",
                {"spam2": "ham2"},
            ),
            (
                {"spam": {"spam1": {"spam2": "ham2", "eggs": "overeasy"}}},
                "spam.spam1.spam2",
                "ham2",
            ),
            (
                {"spam": {"spam1": {"spam2": "ham2", "eggs": "overeasy"}}},
                "spam.spam1.eggs",
                "overeasy",
            ),
            (
                {"spam": {"spam1": {"spam2": "ham2", "eggs": ["over", "easy"]}}},
                "spam.spam1.eggs",
                ["over", "easy"],
            ),
            ({"spam": {"spam1": {"spam2": "ham2", "eggs": 1}}}, "spam.spam1.eggs", 1),
            (
                {"spam": {"spam1": {"spam2": "ham2", "eggs": False}}},
                "spam.spam1.eggs",
                False,
            ),
        ],
    )
    def test_get_property(self, prop_dict, prop_path, expected_value):
        assert _get_property(prop_dict, prop_path) == expected_value

    @pytest.mark.parametrize(
        "prop_dict, prop_path, expected_value, default_value",
        [
            ({}, "spam", "ham", "ham"),
            ({"spam": "ham"}, "eggs", "ham", "ham"),
        ],
    )
    def test_get_property_default(
        self, prop_dict, prop_path, expected_value, default_value
    ):
        assert _get_property(prop_dict, prop_path, default_value) == expected_value

    @pytest.fixture(scope="function")
    def example_config_dict(self) -> Dict[str, str]:
        return {
            "setting1": "value1",
            "setting2": "value2",
            "notifications": {
                "notification_service_type": "twilio_email",
                "nested_setting_2": "nested_value_2",
            },
        }

    @pytest.fixture(scope="function")
    def example_config_record(self, example_config_dict) -> Dict[str, Any]:
        return {"api_set": example_config_dict}

    @pytest.fixture
    def insert_example_config_record(self, db, example_config_record) -> Dict[str, Any]:
        config_record: ApplicationConfig = ApplicationConfig.create_or_update(
            db, data=example_config_record
        )
        assert config_record.api_set == example_config_record["api_set"]
        assert len(db.query(ApplicationConfig).all()) == 1
        config_record_db = db.query(ApplicationConfig).first()
        assert config_record_db.api_set == example_config_record["api_set"]
        assert config_record_db.id == config_record.id
        return config_record.api_set

    @pytest.fixture
    def insert_app_config(self, db):
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.mark.usefixtures("insert_app_config")
    def test_get_resolved_config_property(self, db, insert_example_config_record):
        notification_service_type = ApplicationConfig.get_resolved_config_property(
            db, "notifications.notification_service_type"
        )
        assert (
            notification_service_type
            == insert_example_config_record["notifications"][
                "notification_service_type"
            ]
        )

        # ensure a value that we did not override via API still has
        # its original value returned
        send_request_completion_notification = (
            ApplicationConfig.get_resolved_config_property(
                db, "notifications.send_request_completion_notification"
            )
        )
        assert (
            send_request_completion_notification
            == CONFIG.notifications.send_request_completion_notification
        )


class TestConfigProxy:
    @pytest.fixture(scope="function")
    def example_config_dict(self) -> Dict[str, str]:
        return {
            "setting1": "value1",
            "setting2": "value2",
            "notifications": {
                "notification_service_type": "twilio_email",
                "nested_setting_2": "nested_value_2",
            },
        }

    @pytest.fixture(scope="function")
    def example_config_record(self, example_config_dict) -> Dict[str, Any]:
        return {"api_set": example_config_dict}

    @pytest.fixture
    def insert_example_config_record(self, db, example_config_record) -> Dict[str, Any]:
        config_record: ApplicationConfig = ApplicationConfig.create_or_update(
            db, data=example_config_record
        )
        assert config_record.api_set == example_config_record["api_set"]
        assert len(db.query(ApplicationConfig).all()) == 1
        config_record_db = db.query(ApplicationConfig).first()
        assert config_record_db.api_set == example_config_record["api_set"]
        assert config_record_db.id == config_record.id
        return config_record.api_set

    @pytest.fixture
    def insert_app_config(self, db):
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.fixture
    def insert_app_config_set_notification_service_type_none(self, db):
        service_type = CONFIG.notifications.notification_service_type
        CONFIG.notifications.notification_service_type = None
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        # set back to original value
        CONFIG.notifications.notification_service_type = service_type
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.fixture
    def insert_app_config_set_notifications_none(self, db):
        notifications = CONFIG.notifications
        CONFIG.notifications = None
        ApplicationConfig.update_config_set(db, CONFIG)
        yield
        # set back to original value
        CONFIG.notifications = notifications
        ApplicationConfig.update_config_set(db, CONFIG)

    @pytest.mark.usefixtures("insert_app_config_set_notification_service_type_none")
    def test_config_proxy_none_set(self, config_proxy: ConfigProxy):

        # we've explicitly made sure this property is not set via either traditional config
        # variable or via API
        assert config_proxy.notifications.notification_service_type is None

    @pytest.mark.usefixtures("insert_app_config_set_notification_service_type_none")
    def test_config_proxy_none_set_whole_section(self, config_proxy: ConfigProxy):

        # we've explicitly made sure this whole section is not set via either traditional config
        # variable or via API

        # this property should be None because it's optional
        assert config_proxy.notifications.notification_service_type is None

        # this property is not optional, so we just check it against its default from the traditional config
        assert (
            config_proxy.notifications.send_request_completion_notification
            is CONFIG.notifications.send_request_review_notification
        )

    @pytest.mark.usefixtures("insert_app_config")
    def test_config_proxy(
        self, config_proxy: ConfigProxy, insert_example_config_record
    ):

        notification_service_type = config_proxy.notifications.notification_service_type
        assert (
            notification_service_type
            == insert_example_config_record["notifications"][
                "notification_service_type"
            ]
        )

        # ensure a value that we did not override via API still has
        # its original value returned
        send_request_completion_notification = (
            config_proxy.notifications.send_request_completion_notification
        )
        assert (
            send_request_completion_notification
            == CONFIG.notifications.send_request_completion_notification
        )

    @pytest.mark.usefixtures("insert_app_config")
    def test_config_proxy_unset(
        self, db, config_proxy: ConfigProxy, insert_example_config_record
    ):
        notification_service_type = config_proxy.notifications.notification_service_type
        assert (
            notification_service_type
            == insert_example_config_record["notifications"][
                "notification_service_type"
            ]
        )

        # unset the API-set notification service type property
        ApplicationConfig.update_api_set(
            db, api_set_dict={"notifications": {"notification_service_type": None}}
        )
        notification_service_type = config_proxy.notifications.notification_service_type
        assert (
            notification_service_type == CONFIG.notifications.notification_service_type
        )
