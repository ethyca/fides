from typing import Any, Dict

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from fides.api.models.location_regulation_selections import LocationRegulationSelections

"""
Unit tests for the async functionality in the LocationRegulationSelections class.

These tests are in the `test/ctl` subdir to load async db fixtures correctly.
"""


@pytest.fixture(scope="function")
async def reset_location_regulation_selections(async_session):
    await LocationRegulationSelections.set_selected_locations_async(async_session, [])
    await LocationRegulationSelections.set_selected_regulations_async(async_session, [])
    yield
    await LocationRegulationSelections.set_selected_locations_async(async_session, [])
    await LocationRegulationSelections.set_selected_regulations_async(async_session, [])


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

    async def test_create_or_update_keeps_single_record(
        self,
        async_session: Session,
        data_dict: Dict[str, Any],
    ):
        """
        Ensure create_or_update properly restricts the table to a single record
        """
        config_record: LocationRegulationSelections = (
            await LocationRegulationSelections.create_or_update_async(
                async_session=async_session,
                data=data_dict,
            )
        )
        assert config_record.selected_locations == ["us_ca", "fr"]
        assert config_record.selected_regulations == ["ccpa", "gdpr"]
        async with async_session.begin():
            result = await async_session.execute(select(LocationRegulationSelections))
            config_records_db = result.scalars().all()
            len(config_records_db) == 1
            config_record_db = config_records_db[0]
            assert config_record_db.selected_locations == ["us_ca", "fr"]
            assert config_record_db.selected_regulations == ["ccpa", "gdpr"]
            assert config_record_db.id == config_record.id

        # make a change to locations_selected
        # and assert create_or_update just updates the same single record
        # and assert that unspecified columns are not altered
        data_dict["selected_locations"] = ["us_co"]
        data_dict.pop("selected_regulations")
        new_config_record: LocationRegulationSelections = (
            await LocationRegulationSelections.create_or_update_async(
                async_session=async_session, data=data_dict
            )
        )
        assert new_config_record.selected_locations == ["us_co"]
        assert new_config_record.selected_regulations == [
            "ccpa",
            "gdpr",
        ]  # assert this column was untouched
        assert new_config_record.id == config_record.id
        async with async_session.begin():
            result = await async_session.execute(select(LocationRegulationSelections))
            new_config_records_db = result.scalars().all()
            len(new_config_records_db) == 1
            new_config_record_db = new_config_records_db[0]
            assert new_config_record_db.selected_locations == ["us_co"]
            assert new_config_record_db.selected_regulations == [
                "ccpa",
                "gdpr",
            ]  # assert this column was untouched
            assert new_config_record_db.id == new_config_record.id

    async def test_get_set_locations_regulations_async(
        self,
        async_session,
    ):
        """
        Test async utility methods to get and set locations and regulations
        """
        # ensure we start in a clean state
        assert (
            await LocationRegulationSelections.get_selected_locations_async(
                async_session
            )
            == set()
        )
        # basic selection of locations
        await LocationRegulationSelections.set_selected_locations_async(
            async_session, ["us_ca", "fr"]
        )
        assert await LocationRegulationSelections.get_selected_locations_async(
            async_session
        ) == {
            "us_ca",
            "fr",
        }

        # ensure that values are deduplicated as expected
        await LocationRegulationSelections.set_selected_locations_async(
            async_session, ["us_ca", "fr", "us_ca"]
        )
        assert await LocationRegulationSelections.get_selected_locations_async(
            async_session
        ) == {
            "us_ca",
            "fr",
        }

        # ensure we start in a clean state
        assert (
            await LocationRegulationSelections.get_selected_regulations_async(
                async_session
            )
            == set()
        )
        # basic selection of regulations
        await LocationRegulationSelections.set_selected_regulations_async(
            async_session, ["ccpa", "gdpr"]
        )
        assert await LocationRegulationSelections.get_selected_regulations_async(
            async_session
        ) == {
            "ccpa",
            "gdpr",
        }
        # ensure selected_locations haven't been updated
        assert await LocationRegulationSelections.get_selected_locations_async(
            async_session
        ) == {
            "us_ca",
            "fr",
        }

        # ensure that values are deduplicated as expected
        await LocationRegulationSelections.set_selected_locations_async(
            async_session, ["ccpa", "gdpr", "ccpa"]
        )
        assert await LocationRegulationSelections.get_selected_regulations_async(
            async_session
        ) == {
            "ccpa",
            "gdpr",
        }
