from typing import Any, Dict

import pytest
from sqlalchemy.orm import Session

from fides.api.ops.models.application_settings import ApplicationSettings


class TestApplicationSettingsModel:
    @pytest.fixture(scope="function")
    def example_settings_dict(self) -> Dict[str, str]:
        return {"setting1": "value1", "setting2": "value2"}

    @pytest.fixture(scope="function")
    def example_settings_record(self) -> Dict[str, Any]:
        return {"api_set": {"setting1": "value1", "setting2": "value2"}}

    def test_create_or_update_keeps_single_record(
        self,
        db: Session,
        example_settings_record: Dict[str, Any],
    ):
        """
        Ensure create_or_update properly restricts the table to a single record
        """
        settings_record: ApplicationSettings = ApplicationSettings.create_or_update(
            db, data=example_settings_record
        )
        assert settings_record.api_set == example_settings_record["api_set"]
        assert len(db.query(ApplicationSettings).all()) == 1
        settings_record_db = db.query(ApplicationSettings).first()
        assert settings_record_db.api_set == example_settings_record["api_set"]
        assert settings_record_db.id == settings_record.id

        # make an arbitrary change to settings dict
        # and assert create_or_update just updated the same single record
        example_settings_record["api_set"]["setting3"] = "value3"
        new_settings_record: ApplicationSettings = ApplicationSettings.create_or_update(
            db, data=example_settings_record
        )
        assert new_settings_record.api_set == example_settings_record["api_set"]
        assert new_settings_record.id == settings_record.id
        assert len(db.query(ApplicationSettings).all()) == 1
        new_settings_record_db = db.query(ApplicationSettings).first()
        assert new_settings_record_db.api_set == example_settings_record["api_set"]
        assert new_settings_record_db.id == new_settings_record.id

    def test_create_or_update_merges_settings_dict(
        self,
        db: Session,
        example_settings_record: Dict[str, Any],
    ):
        settings_record: ApplicationSettings = ApplicationSettings.create_or_update(
            db, data=example_settings_record
        )
        assert settings_record.api_set == example_settings_record["api_set"]
        assert len(db.query(ApplicationSettings).all()) == 1
        settings_record_db = db.query(ApplicationSettings).first()
        assert settings_record_db.api_set == example_settings_record["api_set"]
        assert settings_record_db.id == settings_record.id

        # update one setting only
        new_settings_record = {"api_set": {"setting1": "new_value"}}
        settings_record: ApplicationSettings = ApplicationSettings.create_or_update(
            db, data=new_settings_record
        )
        assert settings_record.api_set["setting1"] == "new_value"
        assert settings_record.api_set["setting2"] == "value2"
        assert len(db.query(ApplicationSettings).all()) == 1
        settings_record_db = db.query(ApplicationSettings).first()
        assert settings_record_db.api_set["setting1"] == "new_value"
        assert settings_record_db.api_set["setting2"] == "value2"
        assert settings_record_db.id == settings_record.id

    def test_get_api_settings_nothing_set(
        self,
        db: Session,
    ):
        assert ApplicationSettings.get_api_set_settings(db) == {}

    def test_get_api_settings(
        self, db: Session, example_settings_record: Dict[str, Any]
    ):
        ApplicationSettings.create_or_update(db, data=example_settings_record)
        assert (
            ApplicationSettings.get_api_set_settings(db)
            == example_settings_record["api_set"]
        )
