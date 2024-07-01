from json import dumps
from typing import Any, Dict, Iterable

import pytest
from sqlalchemy.orm import Session

from fides.api.models.application_config import ApplicationConfig
from fides.config import get_config
from fides.config.config_proxy import ConfigProxy

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

    def test_get_api_set_nothing_set(
        self,
        db: Session,
    ):
        db.query(ApplicationConfig).delete()
        assert ApplicationConfig.get_api_set(db) == {}

    def test_get_config_set_nothing_set(
        self,
        db: Session,
    ):
        db.query(ApplicationConfig).delete()
        assert ApplicationConfig.get_config_set(db) == {}

    def test_get_api_config(self, db: Session, example_config_record: Dict[str, Any]):
        ApplicationConfig.create_or_update(db, data=example_config_record)
        assert ApplicationConfig.get_api_set(db) == example_config_record["api_set"]

    def test_update_config_set(self, db):
        ApplicationConfig.update_config_set(db, CONFIG)
        # check a few specific config properties of different types on the database record
        db_config = ApplicationConfig.get_config_set(db)
        assert dumps(db_config, separators=(",", ":")) == CONFIG.model_dump_json()

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
        assert dumps(db_config, separators=(",", ":")) == CONFIG.model_dump_json()

        # reset config values to initial values to ensure we don't mess up any state
        CONFIG.notifications.notification_service_type = notification_service_type
        CONFIG.execution.masking_strict = execution_strict

    def test_update_config_nondict_errors(
        self, db: Session, example_config_record: Dict[str, Any]
    ):
        """
        Test coverage for error path if non-dict is passed into `update` method
        as either the `config_set` key or the `api_set` key
        """
        app_config = ApplicationConfig.create_or_update(db, data=example_config_record)
        with pytest.raises(ValueError):
            app_config.update(db, {"config_set": "invalid"})
        with pytest.raises(ValueError):
            app_config.update(db, {"api_set": "invalid"})


class TestApplicationConfigResolution:
    @pytest.fixture(scope="function")
    def example_config_dict(self) -> Dict[str, str]:
        return {
            "setting1": "value1",
            "setting2": "value2",
            "notifications": {
                "notification_service_type": "twilio_email",
                "nested_setting_2": "nested_value_2",
            },
            "security": {
                "cors_origins": [
                    "http://additionalorigin:8080",
                    "http://localhost",  # this is a _repeated_ value from the config-set values
                ]
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

    def test_get_resolved_config_property_no_config_record(self, db: Session):
        db.query(ApplicationConfig).delete()
        notification_service_type = ApplicationConfig.get_resolved_config_property(
            db, "notifications.notification_service_type"
        )
        assert notification_service_type is None

    @pytest.mark.usefixtures("insert_app_config")
    def test_get_resolved_config_property_merged_values(
        self, db: Session, insert_example_config_record
    ):
        # ensure our config set has cors origins set as a populated list initially, for a valid test
        cors_origins_config_set = ApplicationConfig.get_config_set(db)["security"][
            "cors_origins"
        ]
        assert cors_origins_config_set
        assert isinstance(cors_origins_config_set, Iterable)
        # and ensure there are repeats between our API-set list and our config-set list, for a valid test
        cors_origin_api_set = insert_example_config_record["security"]["cors_origins"]
        repeat_values = set(cors_origin_api_set).intersection(
            set(cors_origins_config_set)
        )
        assert repeat_values

        # now ensure the merging works as expected on resolution
        resolved_origins = ApplicationConfig.get_resolved_config_property(
            db,
            "security.cors_origins",
            merge_values=True,
        )
        for config_set_value in cors_origins_config_set:
            assert config_set_value in resolved_origins
        for api_set_value in cors_origin_api_set:
            assert api_set_value in resolved_origins
        for resolve_origin in resolved_origins:
            assert (
                resolve_origin in cors_origins_config_set
                or resolve_origin in cors_origin_api_set
            )
        assert isinstance(resolved_origins, set)

        # ensure baseline (non-merging) functionality works as expected
        assert sorted(
            ApplicationConfig.get_resolved_config_property(db, "security.cors_origins")
        ) == sorted(cors_origin_api_set)

        # ensure that merging is not performed if either api-set or config-set values aren't present
        insert_example_config_record["security"].pop("cors_origins")
        # clear the api-set cors origin
        ApplicationConfig.clear_api_set(db)
        ApplicationConfig.create_or_update(
            db,
            data={
                "api_set": insert_example_config_record,
            },
        )
        # even if merge is set to true, we should just return config set
        assert (
            ApplicationConfig.get_resolved_config_property(
                db,
                "security.cors_origins",
                merge_values=True,
            )
            == cors_origins_config_set
        )
        # now clear the config-set cors origin
        insert_example_config_record["security"]["cors_origins"] = cors_origin_api_set
        new_config_set = ApplicationConfig.get_config_set(db)
        new_config_set["security"].pop("cors_origins")
        ApplicationConfig.clear_config_set(db)
        ApplicationConfig.create_or_update(
            db,
            data={
                "api_set": insert_example_config_record,
                "config_set": new_config_set,
            },
        )
        # even if merge is set to true, we should just return api set
        assert (
            ApplicationConfig.get_resolved_config_property(
                db,
                "security.cors_origins",
                merge_values=True,
            )
            == cors_origin_api_set
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
            "security": {
                "cors_origins": [
                    "http://additionalorigin:8080",
                    "http://localhost",  # this is a _repeated_ value from the config-set values
                ]
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

    @pytest.mark.usefixtures("insert_app_config")
    def test_config_proxy_merged_values(
        self, db, config_proxy: ConfigProxy, insert_example_config_record
    ):
        """Ensure config proxy properly merges cors_origin api-set and config-set values"""

        # ensure our config set has cors origins set as a populated list initially, for a valid test
        cors_origins_config_set = ApplicationConfig.get_config_set(db)["security"][
            "cors_origins"
        ]
        assert cors_origins_config_set
        assert isinstance(cors_origins_config_set, Iterable)
        # and ensure there are repeats between our API-set list and our config-set list, for a valid test
        cors_origin_api_set = insert_example_config_record["security"]["cors_origins"]
        repeat_values = set(cors_origin_api_set).intersection(
            set(cors_origins_config_set)
        )
        assert repeat_values

        proxy_resolved_cors_origins = config_proxy.security.cors_origins

        for config_set_value in cors_origins_config_set:
            assert config_set_value in proxy_resolved_cors_origins
        for api_set_value in cors_origin_api_set:
            assert api_set_value in proxy_resolved_cors_origins
        for resolve_origin in proxy_resolved_cors_origins:
            assert (
                resolve_origin in cors_origins_config_set
                or resolve_origin in cors_origin_api_set
            )
        assert isinstance(proxy_resolved_cors_origins, set)
