from typing import Any, Dict

import pytest
from sqlalchemy.orm import Session

from fides.api.models.location_regulation_selections import (
    LocationRegulationSelections,
    PrivacyNoticeRegion,
    default_selected_locations,
    filter_regions_by_location,
    group_locations_into_location_groups,
    location_group_to_location,
)


@pytest.fixture(scope="function")
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
        assert config_record_db.selected_location_groups == []
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
        assert config_record_db.selected_location_groups == []
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
        LocationRegulationSelections.set_selected_regulations(
            db, ["ccpa", "gdpr", "ccpa"]
        )
        assert LocationRegulationSelections.get_selected_regulations(db) == {
            "ccpa",
            "gdpr",
        }
        assert LocationRegulationSelections.get_selected_location_groups(db) == set()

        # set locations that make up an entire location group
        LocationRegulationSelections.set_selected_locations(
            db, ["gt", "pa", "ni", "bz", "mx", "sv", "hn", "cr", "us_ca"]
        )

        assert LocationRegulationSelections.get_selected_location_groups(db) == {
            "mexico_central_america",
        }
        assert LocationRegulationSelections.get_selected_locations(db) == {
            "gt",
            "pa",
            "ni",
            "bz",
            "mx",
            "sv",
            "hn",
            "cr",
            "us_ca",
        }

        # Set locations where we are shy of building a full location group
        LocationRegulationSelections.set_selected_locations(
            db, ["gt", "pa", "ni", "bz", "mx", "sv"]
        )
        assert LocationRegulationSelections.get_selected_location_groups(db) == set()


class TestFilterRegionsByLocation:
    base_regions = [
        PrivacyNoticeRegion.us_ca,
        PrivacyNoticeRegion.eea,
        PrivacyNoticeRegion.gb,
        PrivacyNoticeRegion.mexico_central_america,
    ]

    def test_no_locations_or_location_groups_set(self, db):
        """For backwards compatibility if no locations are set, all PrivacyNoticeRegions are available"""
        assert filter_regions_by_location(db, self.base_regions) == self.base_regions

    def test_locations_set(self, db):
        LocationRegulationSelections.set_selected_locations(db, ["us_ca"])

        assert filter_regions_by_location(db, self.base_regions) == [
            PrivacyNoticeRegion.us_ca
        ]

    def test_location_groups_set(self, db):
        # Setting all "mexico_central_america" locations also saves the "mexico_central_america" group
        LocationRegulationSelections.set_selected_locations(
            db, ["gt", "pa", "ni", "bz", "sv", "hn", "cr", "mx"]
        )

        assert filter_regions_by_location(db, self.base_regions) == [
            PrivacyNoticeRegion.mexico_central_america
        ]


class TestGroupLocationsIntoLocationGroups:
    def test_no_locations(self):
        assert group_locations_into_location_groups([]) == set()

    def test_locations_do_not_comprise_full_group(self):
        assert group_locations_into_location_groups(["us_ca"]) == set()

    def test_all_locations_from_a_group_supplied(self):
        assert group_locations_into_location_groups(
            ["gt", "pa", "ni", "bz", "sv", "hn", "cr", "mx"]
        ) == {"mexico_central_america"}


class TestLocationGroupToLocation:
    def test_expected_keys(self):
        """Testing mapping built on startup from location groups to a set of the contained locations from the locations.yml file"""
        assert set(location_group_to_location.keys()) == {
            "eea",
            "mexico_central_america",
            "caribbean",
            "ca",
            "us",
            "non_eea",
        }

    def test_assert_selected_value(self):
        assert location_group_to_location["ca"] == {
            "ca_nb",
            "ca_ab",
            "ca_nt",
            "ca_nu",
            "ca_on",
            "ca_yt",
            "ca_ns",
            "ca_sk",
            "ca_bc",
            "ca_mb",
            "ca_nl",
            "ca_pe",
            "ca_qc",
        }


class TestDefaultSelectedLocations:
    def test_expected_values(self):
        """Test that some of our expected values are default selected"""
        assert isinstance(default_selected_locations, set)

        # somewhat arbitrary set of values to check
        expected_values = [
            "us_ca",  # some US states
            "us_ny",
            "us_co",
            "ca_ab",  # some canadian provinces
            "ca_bc",
            "fr",  # some EEA countries
            "es",
        ]
        not_expected_values = [
            "us",  # location groups should NOT be selected - they will be selected based on locations, automatically
            "ca",
            "eea",
            "tr",  # non EEA countries in Europe should not be selected
            "md"
            "br",  # brazil should not be selected, yet (even though it has a regulation)
            "nz",  # arbitrary other location, new zealand
        ]

        for expected_value in expected_values:
            assert expected_value in default_selected_locations

        for not_expected_value in not_expected_values:
            assert not not_expected_value in default_selected_locations


class TestPrivacyNoticeRegion:
    def test_privacy_notice_region_enum(self):
        with pytest.raises(AttributeError):
            # Regulations not added to enum
            PrivacyNoticeRegion.gdpr

        # Location Groups added
        assert PrivacyNoticeRegion.eea
        assert PrivacyNoticeRegion.mexico_central_america
        assert PrivacyNoticeRegion.caribbean
        assert PrivacyNoticeRegion.us
        assert PrivacyNoticeRegion.ca
        assert PrivacyNoticeRegion.non_eea

        # Locations added - just asserting selected locations
        assert PrivacyNoticeRegion.us_ca
        assert PrivacyNoticeRegion.ca_nl
        assert PrivacyNoticeRegion.fr
        assert PrivacyNoticeRegion.gb
        assert PrivacyNoticeRegion.mx

        # Continents not added
        with pytest.raises(AttributeError):
            # Regulations not added to enum
            PrivacyNoticeRegion.Asia
