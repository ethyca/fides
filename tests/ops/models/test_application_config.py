from typing import Any, Dict

import pytest
from sqlalchemy.orm import Session

from fides.api.ops.models.application_config import ApplicationConfig


class TestApplicationConfigModel:
    @pytest.fixture(scope="function")
    def example_config_dict(self) -> Dict[str, str]:
        return {"setting1": "value1", "setting2": "value2"}

    @pytest.fixture(scope="function")
    def example_config_record(self) -> Dict[str, Any]:
        return {"api_set": {"setting1": "value1", "setting2": "value2"}}

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
        example_config_record["api_set"]["setting3"] = "value3"
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

    def test_get_api_config_nothing_set(
        self,
        db: Session,
    ):
        assert ApplicationConfig.get_api_set_config(db) == {}

    def test_get_api_config(self, db: Session, example_config_record: Dict[str, Any]):
        ApplicationConfig.create_or_update(db, data=example_config_record)
        assert (
            ApplicationConfig.get_api_set_config(db) == example_config_record["api_set"]
        )
