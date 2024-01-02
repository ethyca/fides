from json import dumps
from typing import Any, Dict

import pytest
from sqlalchemy.orm import Session

from fides.api.models.location_regulation_selections import LocationRegulationSelections


@pytest.fixture(scope="function", autouse=True)
def reset_location_regulation_selections(db):
    LocationRegulationSelections.set_selected_locations(db, [])
    LocationRegulationSelections.set_selected_regulations(db, [])
    yield
    LocationRegulationSelections.set_selected_locations(db, [])
    LocationRegulationSelections.set_selected_regulations(db, [])


class TestLocationRegulationSelections:
    @pytest.fixture
    def data_dict(self) -> Dict:
        """Sample update data dict"""
        return {
            "selected_locations": [
                "us_ca",
                "fr",
            ],
            "selected_regulations": [
                "ccpa",
                "gdpr",
            ],
        }

    def test_create_or_update_keeps_single_record(
        self,
        db: Session,
        data_dict: Dict[str, Any],
    ):
        """
        Ensure create_or_update properly restricts the table to a single record
        """

        config_record: LocationRegulationSelections = (
            LocationRegulationSelections.create_or_update(
                db,
                data=data_dict,
            )
        )
        assert config_record.selected_locations == ["us_ca", "fr"]
        assert config_record.selected_regulations == ["ccpa", "gdpr"]
        assert len(db.query(LocationRegulationSelections).all()) == 1
        config_record_db = db.query(LocationRegulationSelections).first()
        assert config_record_db.selected_locations == ["us_ca", "fr"]
        assert config_record_db.selected_regulations == ["ccpa", "gdpr"]
        assert config_record_db.id == config_record.id

        # make a change to locations_selected
        # and assert create_or_update just updates the same single record
        # and assert that unspecified columns are not altered
        data_dict["selected_locations"] = ["us_co"]
        data_dict.pop("selected_regulations")
        new_config_record: LocationRegulationSelections = (
            LocationRegulationSelections.create_or_update(db, data=data_dict)
        )
        assert new_config_record.selected_locations == ["us_co"]
        assert new_config_record.selected_regulations == [
            "ccpa",
            "gdpr",
        ]  # assert this column was untouched
        assert new_config_record.id == config_record.id
        assert len(db.query(LocationRegulationSelections).all()) == 1
        new_config_record_db = db.query(LocationRegulationSelections).first()
        assert new_config_record_db.selected_locations == ["us_co"]
        assert new_config_record_db.selected_regulations == [
            "ccpa",
            "gdpr",
        ]  # assert this column was untouched
        assert new_config_record_db.id == new_config_record.id

    def test_get_set_locations_regulations(
        self,
        db: Session,
    ):
        """
        Test utility methods to get and set locations and regulations
        """
        # ensure we start in a clean state
        assert LocationRegulationSelections.get_selected_locations(db) == set()
        # basic selection of locations
        LocationRegulationSelections.set_selected_locations(db, ["us_ca", "fr"])
        assert LocationRegulationSelections.get_selected_locations(db) == {
            "us_ca",
            "fr",
        }

        # ensure that values are deduplicated as expected
        LocationRegulationSelections.set_selected_locations(
            db, ["us_ca", "fr", "us_ca"]
        )
        assert LocationRegulationSelections.get_selected_locations(db) == {
            "us_ca",
            "fr",
        }

        # ensure we start in a clean state
        assert LocationRegulationSelections.get_selected_regulations(db) == set()
        # basic selection of regulations
        LocationRegulationSelections.set_selected_regulations(db, ["ccpa", "gdpr"])
        assert LocationRegulationSelections.get_selected_regulations(db) == {
            "ccpa",
            "gdpr",
        }
        # ensure selected_locations haven't been updated
        assert LocationRegulationSelections.get_selected_locations(db) == {
            "us_ca",
            "fr",
        }

        # ensure that values are deduplicated as expected
        LocationRegulationSelections.set_selected_locations(
            db, ["ccpa", "gdpr", "ccpa"]
        )
        assert LocationRegulationSelections.get_selected_regulations(db) == {
            "ccpa",
            "gdpr",
        }
