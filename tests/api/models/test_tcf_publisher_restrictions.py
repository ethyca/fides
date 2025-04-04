from typing import AsyncGenerator, Generator

import pytest
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fides.api.models.tcf_publisher_restrictions import (
    TCFConfiguration,
    TCFPublisherRestriction,
    TCFRestrictionType,
    TCFVendorRestriction,
)


class TestCreateTCFPublisherRestrictionAsync:
    """
    Same tests as in TestCreateTCFPublisherRestriction, but using the create_async method.
    """

    @pytest.fixture
    async def existing_restriction(
        self, async_session: AsyncSession, tcf_config: TCFConfiguration
    ) -> AsyncGenerator[TCFPublisherRestriction, None]:
        """Create an existing restriction for testing updates."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": 2,
            "restriction_type": TCFRestrictionType.require_consent,
            "vendor_restriction": TCFVendorRestriction.allow_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 1, "end_vendor_id": 5},
                {"start_vendor_id": 7, "end_vendor_id": 10},
            ],
        }
        restriction = await TCFPublisherRestriction.create_async(
            async_db=async_session, data=data
        )
        yield restriction

        await async_session.delete(restriction)
        await async_session.commit()

    @pytest.fixture
    async def tcf_config(
        self, async_session: AsyncSession
    ) -> AsyncGenerator[TCFConfiguration, None]:
        """Create a TCF configuration for testing."""
        async with async_session.begin():
            insert_stmt = insert(TCFConfiguration).values(
                {"name": "test-config", "id": "test-config"}
            )
            result = await async_session.execute(insert_stmt)
            record_id = result.inserted_primary_key.id

            config = await async_session.execute(
                select(TCFConfiguration).where(TCFConfiguration.id == record_id)
            )
            config = config.scalars().first()

        yield config

        await async_session.delete(config)
        await async_session.commit()

    async def test_create_valid_restriction(
        self, async_session: AsyncSession, tcf_config: TCFConfiguration
    ) -> None:
        """Test creating a valid publisher restriction."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": 8,
            "restriction_type": TCFRestrictionType.require_consent,
            "vendor_restriction": TCFVendorRestriction.allow_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 1, "end_vendor_id": 5},
                {"start_vendor_id": 7, "end_vendor_id": 10},
            ],
        }
        restriction = await TCFPublisherRestriction.create_async(
            async_db=async_session, data=data
        )
        assert restriction.purpose_id == 8
        assert len(restriction.range_entries) == 2
        assert restriction.range_entries[0]["start_vendor_id"] == 1
        assert restriction.range_entries[0]["end_vendor_id"] == 5
        assert restriction.range_entries[1]["start_vendor_id"] == 7
        assert restriction.range_entries[1]["end_vendor_id"] == 10

        # Test that the restriction is created in the database
        restriction = await async_session.execute(
            select(TCFPublisherRestriction).where(
                TCFPublisherRestriction.id == restriction.id
            )
        )
        restriction = restriction.scalars().first()
        assert restriction is not None
        assert len(restriction.range_entries) == 2

    async def test_invalid_range_entry(
        self, async_session: AsyncSession, tcf_config: TCFConfiguration
    ) -> None:
        """Test that creating a restriction with invalid range entry fails."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": 8,
            "restriction_type": TCFRestrictionType.purpose_restriction,
            "vendor_restriction": TCFVendorRestriction.allow_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 5, "end_vendor_id": 1},  # end < start
            ],
        }

        with pytest.raises(
            ValueError, match="end_vendor_id must be greater than start_vendor_id"
        ):
            await TCFPublisherRestriction.create_async(
                async_db=async_session, data=data
            )

    @pytest.mark.parametrize(
        "range_entries",
        [
            pytest.param(
                [
                    {"start_vendor_id": 1, "end_vendor_id": 5},
                    {"start_vendor_id": 18, "end_vendor_id": 25},
                    {"start_vendor_id": 3, "end_vendor_id": 7},
                ],
                id="overlapping_middle",
            ),
            pytest.param(
                [
                    {"start_vendor_id": 1, "end_vendor_id": 5},
                    {"start_vendor_id": 5, "end_vendor_id": 10},
                ],
                id="touching_endpoints",
            ),
            pytest.param(
                [
                    {"start_vendor_id": 1, "end_vendor_id": 10},
                    {"start_vendor_id": 5, "end_vendor_id": 7},
                ],
                id="nested_range",
            ),
            pytest.param(
                [
                    {"start_vendor_id": 1, "end_vendor_id": 5},
                    {"start_vendor_id": 2, "end_vendor_id": 3},
                    {"start_vendor_id": 4, "end_vendor_id": 6},
                ],
                id="multiple_overlaps",
            ),
        ],
    )
    async def test_overlapping_ranges(
        self,
        async_session: AsyncSession,
        tcf_config: TCFConfiguration,
        range_entries: list,
    ) -> None:
        """Test that creating a restriction with overlapping ranges fails."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": 8,
            "restriction_type": TCFRestrictionType.require_legitimate_interest,
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": range_entries,
        }
        with pytest.raises(ValueError, match="Overlapping ranges found"):
            await TCFPublisherRestriction.create_async(
                async_db=async_session, data=data
            )

    async def test_overlapping_ranges_with_existing_restriction(
        self,
        async_session: AsyncSession,
        tcf_config: TCFConfiguration,
        existing_restriction: TCFPublisherRestriction,
    ) -> None:
        """Test that creating a restriction with ranges overlapping a different restriction fails."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": existing_restriction.purpose_id,
            "restriction_type": TCFRestrictionType.require_legitimate_interest,
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": [{"start_vendor_id": 3, "end_vendor_id": 6}],
        }
        with pytest.raises(ValueError, match="Overlapping ranges found"):
            await TCFPublisherRestriction.create_async(
                async_db=async_session, data=data
            )

    async def test_restrict_all_vendors_with_entries(
        self, async_session: AsyncSession, tcf_config: TCFConfiguration
    ) -> None:
        """Test that restrict_all_vendors cannot have range entries."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": 8,
            "restriction_type": TCFRestrictionType.require_legitimate_interest,
            "vendor_restriction": TCFVendorRestriction.restrict_all_vendors,
            "range_entries": [
                {"start_vendor_id": 1, "end_vendor_id": 5},
            ],
        }
        with pytest.raises(
            ValueError, match="restrict_all_vendors cannot have any range entries"
        ):
            await TCFPublisherRestriction.create_async(
                async_db=async_session, data=data
            )

    async def test_single_vendor_range(
        self, async_session: AsyncSession, tcf_config: TCFConfiguration
    ) -> None:
        """Test creating a restriction with a single vendor (no end_vendor_id)."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": 8,
            "restriction_type": TCFRestrictionType.require_consent,
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 1},  # Single vendor
            ],
        }
        restriction = await TCFPublisherRestriction.create_async(
            async_db=async_session, data=data
        )
        assert len(restriction.range_entries) == 1
        assert restriction.range_entries[0]["start_vendor_id"] == 1
        assert restriction.range_entries[0]["end_vendor_id"] is None

        # Test that the restriction is created in the database
        restriction = await async_session.execute(
            select(TCFPublisherRestriction).where(
                TCFPublisherRestriction.id == restriction.id
            )
        )
        restriction = restriction.scalars().first()
        assert restriction is not None
        assert restriction.restriction_type == TCFRestrictionType.require_consent
        assert (
            restriction.vendor_restriction
            == TCFVendorRestriction.restrict_specific_vendors
        )

    async def test_restrict_all_no_range_entries(
        self, async_session: AsyncSession, tcf_config: TCFConfiguration
    ) -> None:
        """Test that restrict_all_vendors without range entries is valid."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": 8,
            "restriction_type": TCFRestrictionType.purpose_restriction,
            "vendor_restriction": TCFVendorRestriction.restrict_all_vendors,
            "range_entries": [],
        }
        restriction = await TCFPublisherRestriction.create_async(
            async_db=async_session, data=data
        )
        assert restriction.range_entries == []

        # Test that the restriction is created in the database
        restriction = await async_session.execute(
            select(TCFPublisherRestriction).where(
                TCFPublisherRestriction.id == restriction.id
            )
        )
        restriction = restriction.scalars().first()
        assert restriction is not None
        assert restriction.range_entries == []
        assert restriction.restriction_type == TCFRestrictionType.purpose_restriction
        assert (
            restriction.vendor_restriction == TCFVendorRestriction.restrict_all_vendors
        )


class TestTCFPublisherRestrictionInstantiation:
    """
    Test that the TCFPublisherRestriction instantiation validates the data.
    """

    @pytest.fixture
    def tcf_config(self, db: Session) -> Generator[TCFConfiguration, None, None]:
        """Create a TCF configuration for testing."""
        config = TCFConfiguration.create(
            db=db,
            data={"name": "test-config", "id": "test-config"},
        )
        yield config
        # Cleanup
        config.delete(db)

    @pytest.mark.parametrize(
        "range_entries",
        [
            pytest.param(
                [
                    {"start_vendor_id": 1, "end_vendor_id": 5},
                    {"start_vendor_id": 18, "end_vendor_id": 25},
                    {"start_vendor_id": 3, "end_vendor_id": 7},
                ],
                id="overlapping_middle",
            ),
            pytest.param(
                [
                    {"start_vendor_id": 1, "end_vendor_id": 5},
                    {"start_vendor_id": 5, "end_vendor_id": 10},
                ],
                id="touching_endpoints",
            ),
            pytest.param(
                [
                    {"start_vendor_id": 1, "end_vendor_id": 10},
                    {"start_vendor_id": 5, "end_vendor_id": 7},
                ],
                id="nested_range",
            ),
            pytest.param(
                [
                    {"start_vendor_id": 1, "end_vendor_id": 5},
                    {"start_vendor_id": 2, "end_vendor_id": 3},
                    {"start_vendor_id": 4, "end_vendor_id": 6},
                ],
                id="multiple_overlaps",
            ),
        ],
    )
    def test_overlapping_ranges(
        self, tcf_config: TCFConfiguration, range_entries: list
    ) -> None:
        with pytest.raises(ValueError, match="Overlapping ranges found"):
            TCFPublisherRestriction(
                tcf_configuration_id=tcf_config.id,
                purpose_id=2,
                restriction_type=TCFRestrictionType.require_legitimate_interest,
                vendor_restriction=TCFVendorRestriction.allow_specific_vendors,
                range_entries=range_entries,
            )

    def test_restrict_all_vendors_with_entries(
        self, tcf_config: TCFConfiguration
    ) -> None:
        with pytest.raises(
            ValueError, match="restrict_all_vendors cannot have any range entries"
        ):
            TCFPublisherRestriction(
                tcf_configuration_id=tcf_config.id,
                purpose_id=11,
                restriction_type=TCFRestrictionType.require_legitimate_interest,
                vendor_restriction=TCFVendorRestriction.restrict_all_vendors,
                range_entries=[{"start_vendor_id": 1, "end_vendor_id": 5}],
            )

    def test_invalid_range_entry(self, tcf_config: TCFConfiguration) -> None:
        with pytest.raises(
            ValueError, match="end_vendor_id must be greater than start_vendor_id"
        ):
            TCFPublisherRestriction(
                tcf_configuration_id=tcf_config.id,
                purpose_id=2,
                restriction_type=TCFRestrictionType.require_consent,
                vendor_restriction=TCFVendorRestriction.allow_specific_vendors,
                range_entries=[{"start_vendor_id": 5, "end_vendor_id": 1}],
            )

    def test_valid_restriction(self, db: Session, tcf_config: TCFConfiguration) -> None:
        """Test creating a valid publisher restriction."""
        restriction = TCFPublisherRestriction(
            tcf_configuration_id=tcf_config.id,
            purpose_id=2,
            restriction_type=TCFRestrictionType.require_consent,
            vendor_restriction=TCFVendorRestriction.allow_specific_vendors,
            range_entries=[
                {"start_vendor_id": 1, "end_vendor_id": 5},
                {"start_vendor_id": 7, "end_vendor_id": 10},
            ],
        )

        assert restriction.purpose_id == 2
        assert len(restriction.range_entries) == 2
        assert restriction.range_entries[0]["start_vendor_id"] == 1
        assert restriction.range_entries[0]["end_vendor_id"] == 5
        assert restriction.range_entries[1]["start_vendor_id"] == 7
        assert restriction.range_entries[1]["end_vendor_id"] == 10


class TestUpdateTCFPublisherRestrictionAsync:
    """Test cases for the update_async method of TCFPublisherRestriction."""

    @pytest.fixture
    async def tcf_config(
        self, async_session: AsyncSession
    ) -> AsyncGenerator[TCFConfiguration, None]:
        """Create a TCF configuration for testing."""
        async with async_session.begin():
            insert_stmt = insert(TCFConfiguration).values(
                {"name": "test-config", "id": "test-config"}
            )
            result = await async_session.execute(insert_stmt)
            record_id = result.inserted_primary_key.id

            config = await async_session.execute(
                select(TCFConfiguration).where(TCFConfiguration.id == record_id)
            )
            config = config.scalars().first()

        yield config

        await async_session.delete(config)
        await async_session.commit()

    @pytest.fixture
    async def existing_restriction(
        self, async_session: AsyncSession, tcf_config: TCFConfiguration
    ) -> AsyncGenerator[TCFPublisherRestriction, None]:
        """Create an existing restriction for testing updates."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": 8,
            "restriction_type": TCFRestrictionType.require_consent,
            "vendor_restriction": TCFVendorRestriction.allow_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 1, "end_vendor_id": 5},
                {"start_vendor_id": 7, "end_vendor_id": 10},
            ],
        }
        restriction = await TCFPublisherRestriction.create_async(
            async_db=async_session, data=data
        )
        yield restriction

        await async_session.delete(restriction)
        await async_session.commit()

    async def test_update_valid_restriction(
        self,
        async_session: AsyncSession,
        existing_restriction: TCFPublisherRestriction,
    ) -> None:
        """Test updating a restriction with valid data."""
        update_data = {
            "restriction_type": TCFRestrictionType.require_legitimate_interest,
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 15, "end_vendor_id": 20},
                {"start_vendor_id": 25, "end_vendor_id": 30},
            ],
        }
        updated = await existing_restriction.update_async(
            async_db=async_session, data=update_data
        )

        # Verify the update was successful
        assert (
            updated.restriction_type == TCFRestrictionType.require_legitimate_interest
        )
        assert (
            updated.vendor_restriction == TCFVendorRestriction.restrict_specific_vendors
        )
        assert len(updated.range_entries) == 2
        assert updated.range_entries[0]["start_vendor_id"] == 15
        assert updated.range_entries[0]["end_vendor_id"] == 20
        assert updated.range_entries[1]["start_vendor_id"] == 25
        assert updated.range_entries[1]["end_vendor_id"] == 30

        # Verify the update persisted in the database
        db_restriction = await async_session.execute(
            select(TCFPublisherRestriction).where(
                TCFPublisherRestriction.id == existing_restriction.id
            )
        )
        db_restriction = db_restriction.scalars().first()
        assert db_restriction is not None
        assert (
            db_restriction.restriction_type
            == TCFRestrictionType.require_legitimate_interest
        )
        assert (
            db_restriction.vendor_restriction
            == TCFVendorRestriction.restrict_specific_vendors
        )
        assert len(db_restriction.range_entries) == 2

    async def test_update_invalid_range_entry(
        self,
        async_session: AsyncSession,
        existing_restriction: TCFPublisherRestriction,
    ) -> None:
        """Test that updating with invalid range entry fails."""
        update_data = {
            "range_entries": [
                {"start_vendor_id": 5, "end_vendor_id": 1},  # end < start
            ],
        }
        with pytest.raises(
            ValueError, match="end_vendor_id must be greater than start_vendor_id"
        ):
            await existing_restriction.update_async(
                async_db=async_session, data=update_data
            )

    async def test_update_overlapping_ranges(
        self,
        async_session: AsyncSession,
        existing_restriction: TCFPublisherRestriction,
    ) -> None:
        """Test that updating with overlapping ranges fails."""
        update_data = {
            "vendor_restriction": existing_restriction.vendor_restriction,
            "range_entries": [
                {"start_vendor_id": 1, "end_vendor_id": 10},
                {
                    "start_vendor_id": 5,
                    "end_vendor_id": 15,
                },  # Overlaps with first range
            ],
        }
        with pytest.raises(ValueError, match="Overlapping ranges found"):
            await existing_restriction.update_async(
                async_db=async_session, data=update_data
            )

    async def test_update_restrict_all_vendors_with_entries(
        self,
        async_session: AsyncSession,
        existing_restriction: TCFPublisherRestriction,
    ) -> None:
        """Test that updating to restrict_all_vendors with range entries fails."""
        update_data = {
            "vendor_restriction": TCFVendorRestriction.restrict_all_vendors,
            "range_entries": [
                {"start_vendor_id": 1, "end_vendor_id": 5},
            ],
        }
        with pytest.raises(
            ValueError, match="restrict_all_vendors cannot have any range entries"
        ):
            await existing_restriction.update_async(
                async_db=async_session, data=update_data
            )

    async def test_update_single_vendor_range(
        self,
        async_session: AsyncSession,
        existing_restriction: TCFPublisherRestriction,
    ) -> None:
        """Test updating to a single vendor range (no end_vendor_id)."""
        update_data = {
            "vendor_restriction": existing_restriction.vendor_restriction,
            "range_entries": [
                {"start_vendor_id": 1},  # Single vendor
            ],
        }
        updated = await existing_restriction.update_async(
            async_db=async_session, data=update_data
        )
        assert len(updated.range_entries) == 1
        assert updated.range_entries[0]["start_vendor_id"] == 1
        assert updated.range_entries[0]["end_vendor_id"] is None

    async def test_update_overlapping_with_existing_purpose(
        self,
        async_session: AsyncSession,
        tcf_config: TCFConfiguration,
        existing_restriction: TCFPublisherRestriction,
    ) -> None:
        """Test that updating ranges that would overlap with another restriction for the same purpose fails."""
        # Create another restriction for the same purpose
        other_data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": existing_restriction.purpose_id,  # Same purpose
            "restriction_type": TCFRestrictionType.require_consent,
            "vendor_restriction": TCFVendorRestriction.allow_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 20, "end_vendor_id": 25},
            ],
        }
        other_restriction = await TCFPublisherRestriction.create_async(
            async_db=async_session, data=other_data
        )

        # Try to update the first restriction with ranges that would overlap with the second
        update_data = {
            "vendor_restriction": existing_restriction.vendor_restriction,
            "range_entries": [
                {
                    "start_vendor_id": 15,
                    "end_vendor_id": 22,
                },  # Overlaps with other restriction
            ],
        }
        with pytest.raises(ValueError, match="Overlapping ranges found"):
            await existing_restriction.update_async(
                async_db=async_session, data=update_data
            )

        # Cleanup
        await async_session.delete(other_restriction)
        await async_session.commit()
