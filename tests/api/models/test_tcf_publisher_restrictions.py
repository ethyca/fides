from typing import AsyncGenerator, Generator

import pytest
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fides.api.models.tcf_publisher_restrictions import (
    RangeEntry,
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
    async def existing_restriction_restrict_all(
        self, async_session: AsyncSession, tcf_config: TCFConfiguration
    ) -> AsyncGenerator[TCFPublisherRestriction, None]:
        """Create an existing restriction with restrict_all_vendors for testing."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": 3,
            "restriction_type": TCFRestrictionType.require_consent,
            "vendor_restriction": TCFVendorRestriction.restrict_all_vendors,
            "range_entries": [],
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

    def test_create_sync_throws_error(
        self, db: Session, tcf_config: TCFConfiguration
    ) -> None:
        """
        Test that the sync create method throws an error telling users to use the async method.
        """
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
        with pytest.raises(NotImplementedError, match="Use create_async instead"):
            TCFPublisherRestriction.create(db=db, data=data)

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
            ValueError,
            match="end_vendor_id must be greater than or equal to start_vendor_id",
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
            ValueError,
            match="A restrict_all_vendors restriction cannot have any range entries",
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

    async def test_create_with_same_restriction_type(
        self,
        async_session: AsyncSession,
        tcf_config: TCFConfiguration,
        existing_restriction: TCFPublisherRestriction,
    ) -> None:
        """Test that creating a restriction with the same restriction type for a purpose fails."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": existing_restriction.purpose_id,
            "restriction_type": existing_restriction.restriction_type,  # Same restriction type
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 20, "end_vendor_id": 25}
            ],  # Different range
        }
        with pytest.raises(
            ValueError,
            match=f"Invalid {existing_restriction.restriction_type} restriction for purpose {existing_restriction.purpose_id}: a restriction of this type already exists for this purpose.",
        ):
            await TCFPublisherRestriction.create_async(
                async_db=async_session, data=data
            )

    async def test_create_with_existing_restrict_all(
        self,
        async_session: AsyncSession,
        tcf_config: TCFConfiguration,
        existing_restriction_restrict_all: TCFPublisherRestriction,
    ) -> None:
        """Test that creating any restriction for a purpose that has a restrict_all_vendors restriction fails."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": existing_restriction_restrict_all.purpose_id,
            "restriction_type": TCFRestrictionType.require_legitimate_interest,  # Different type
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": [{"start_vendor_id": 1, "end_vendor_id": 5}],
        }
        with pytest.raises(
            ValueError,
            match=f"Invalid restriction for purpose {existing_restriction_restrict_all.purpose_id}: a restrict_all_vendors restriction exists for this purpose.",
        ):
            await TCFPublisherRestriction.create_async(
                async_db=async_session, data=data
            )

    async def test_create_restrict_all_with_existing_restrictions(
        self,
        async_session: AsyncSession,
        tcf_config: TCFConfiguration,
        existing_restriction: TCFPublisherRestriction,
    ) -> None:
        """Test that creating a restrict_all_vendors restriction for a purpose that has other restrictions fails."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": existing_restriction.purpose_id,
            "restriction_type": TCFRestrictionType.require_legitimate_interest,
            "vendor_restriction": TCFVendorRestriction.restrict_all_vendors,
            "range_entries": [],
        }
        with pytest.raises(
            ValueError,
            match=f"Invalid restrict_all_vendors restriction for purpose {existing_restriction.purpose_id}: other restrictions already exist for this purpose.",
        ):
            await TCFPublisherRestriction.create_async(
                async_db=async_session, data=data
            )

    async def test_create_overlapping_allow_and_restrict_vendors(
        self,
        async_session: AsyncSession,
        tcf_config: TCFConfiguration,
        existing_restriction: TCFPublisherRestriction,
    ) -> None:
        """Test that creating a restriction that overlaps with transformed allowlist ranges fails."""
        # The existing restriction allows vendors 1-5 and 7-10
        # So the transformed ranges are: 6, 11-9999
        # Creating a restriction for vendors 6 or 11-9999 should fail
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": existing_restriction.purpose_id,
            "restriction_type": TCFRestrictionType.require_legitimate_interest,
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 6}
            ],  # Overlaps with transformed range
        }
        with pytest.raises(ValueError, match="Overlapping ranges found"):
            await TCFPublisherRestriction.create_async(
                async_db=async_session, data=data
            )

    async def test_create_non_overlapping_mixed_vendor_restrictions(
        self,
        async_session: AsyncSession,
        tcf_config: TCFConfiguration,
        existing_restriction: TCFPublisherRestriction,
    ) -> None:
        """Test that creating a restriction with non-overlapping ranges succeeds."""
        # The existing restriction allows vendors 1-5 and 7-10
        # So we can create a new restriction that allows vendors 2-4 (subset of 1-5)
        # since this will not overlap with the transformed ranges (6, 11-9999)
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": existing_restriction.purpose_id,
            "restriction_type": TCFRestrictionType.require_legitimate_interest,  # Different type
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 2, "end_vendor_id": 4}
            ],  # Subset of allowed range
        }
        restriction = await TCFPublisherRestriction.create_async(
            async_db=async_session, data=data
        )
        assert restriction is not None
        assert len(restriction.range_entries) == 1
        assert restriction.range_entries[0]["start_vendor_id"] == 2
        assert restriction.range_entries[0]["end_vendor_id"] == 4

    async def test_create_allow_specific_vendors_no_entries(
        self,
        async_session: AsyncSession,
        tcf_config: TCFConfiguration,
    ) -> None:
        """Test that creating a allow_specific_vendors restriction with no range entries fails."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": 8,
            "restriction_type": TCFRestrictionType.require_consent,
            "vendor_restriction": TCFVendorRestriction.allow_specific_vendors,
            "range_entries": [],  # Empty range entries
        }
        with pytest.raises(
            ValueError,
            match="A allow_specific_vendors restriction must have at least one range entry",
        ):
            await TCFPublisherRestriction.create_async(
                async_db=async_session, data=data
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
            ValueError,
            match="A restrict_all_vendors restriction cannot have any range entries",
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
            ValueError,
            match="end_vendor_id must be greater than or equal to start_vendor_id",
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
    async def existing_restriction_allow_specific_vendors(
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

    @pytest.fixture
    async def existing_restriction_restrict_specific_vendors(
        self, async_session: AsyncSession, tcf_config: TCFConfiguration
    ) -> AsyncGenerator[TCFPublisherRestriction, None]:
        """Create an existing restriction with restrict_specific_vendors for testing."""
        data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": 8,
            "restriction_type": TCFRestrictionType.require_legitimate_interest,
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 15, "end_vendor_id": 20},
                {"start_vendor_id": 25, "end_vendor_id": 30},
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
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
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
        updated = await existing_restriction_allow_specific_vendors.update_async(
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
                TCFPublisherRestriction.id
                == existing_restriction_allow_specific_vendors.id
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
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test that updating with invalid range entry fails."""
        update_data = {
            "range_entries": [
                {"start_vendor_id": 5, "end_vendor_id": 1},  # end < start
            ],
        }
        with pytest.raises(
            ValueError,
            match="end_vendor_id must be greater than or equal to start_vendor_id",
        ):
            await existing_restriction_allow_specific_vendors.update_async(
                async_db=async_session, data=update_data
            )

    async def test_update_overlapping_ranges(
        self,
        async_session: AsyncSession,
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test that updating with overlapping ranges fails."""
        update_data = {
            "vendor_restriction": existing_restriction_allow_specific_vendors.vendor_restriction,
            "range_entries": [
                {"start_vendor_id": 1, "end_vendor_id": 10},
                {
                    "start_vendor_id": 5,
                    "end_vendor_id": 15,
                },  # Overlaps with first range
            ],
        }
        with pytest.raises(ValueError, match="Overlapping ranges found"):
            await existing_restriction_allow_specific_vendors.update_async(
                async_db=async_session, data=update_data
            )

    async def test_update_restrict_all_vendors_with_entries(
        self,
        async_session: AsyncSession,
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test that updating to restrict_all_vendors with range entries fails."""
        update_data = {
            "vendor_restriction": TCFVendorRestriction.restrict_all_vendors,
            "range_entries": [
                {"start_vendor_id": 1, "end_vendor_id": 5},
            ],
        }
        with pytest.raises(
            ValueError,
            match="A restrict_all_vendors restriction cannot have any range entries",
        ):
            await existing_restriction_allow_specific_vendors.update_async(
                async_db=async_session, data=update_data
            )

    async def test_update_single_vendor_range(
        self,
        async_session: AsyncSession,
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test updating to a single vendor range (no end_vendor_id)."""
        update_data = {
            "vendor_restriction": existing_restriction_allow_specific_vendors.vendor_restriction,
            "range_entries": [
                {"start_vendor_id": 1},  # Single vendor
            ],
        }
        updated = await existing_restriction_allow_specific_vendors.update_async(
            async_db=async_session, data=update_data
        )
        assert len(updated.range_entries) == 1
        assert updated.range_entries[0]["start_vendor_id"] == 1
        assert updated.range_entries[0]["end_vendor_id"] is None

    async def test_update_overlapping_with_existing_purpose(
        self,
        async_session: AsyncSession,
        tcf_config: TCFConfiguration,
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test that updating ranges that would overlap with another restriction for the same purpose fails."""
        # Create another restriction for the same purpose
        other_data = {
            "tcf_configuration_id": tcf_config.id,
            "purpose_id": existing_restriction_allow_specific_vendors.purpose_id,  # Same purpose
            "restriction_type": TCFRestrictionType.require_legitimate_interest,  # Different restriction type
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 8},
                {"start_vendor_id": 2, "end_vendor_id": 3},
            ],
        }
        other_restriction = await TCFPublisherRestriction.create_async(
            async_db=async_session, data=other_data
        )

        # Try to update the first restriction with ranges that would overlap with the second
        update_data = {
            "range_entries": [
                {
                    "start_vendor_id": 15,
                    "end_vendor_id": 22,
                },  # Overlaps with other restriction
            ],
        }
        with pytest.raises(ValueError, match="Overlapping ranges found"):
            await existing_restriction_allow_specific_vendors.update_async(
                async_db=async_session, data=update_data
            )

        # Cleanup
        await async_session.delete(other_restriction)
        await async_session.commit()

    async def test_update_to_restrict_all_vendors_no_entries(
        self,
        async_session: AsyncSession,
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test updating to restrict_all_vendors with no range entries."""
        update_data = {
            "vendor_restriction": TCFVendorRestriction.restrict_all_vendors,
            "range_entries": [],
        }
        updated = await existing_restriction_allow_specific_vendors.update_async(
            async_db=async_session, data=update_data
        )
        assert updated.vendor_restriction == TCFVendorRestriction.restrict_all_vendors
        assert len(updated.range_entries) == 0

    async def test_update_from_allow_to_restrict_specific_vendors(
        self,
        async_session: AsyncSession,
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test updating from allow_specific_vendors to restrict_specific_vendors."""
        update_data = {
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": [
                {
                    "start_vendor_id": 50,
                    "end_vendor_id": 55,
                },  # New non-overlapping range
            ],
        }
        updated = await existing_restriction_allow_specific_vendors.update_async(
            async_db=async_session, data=update_data
        )
        assert (
            updated.vendor_restriction == TCFVendorRestriction.restrict_specific_vendors
        )
        assert len(updated.range_entries) == 1
        assert updated.range_entries[0]["start_vendor_id"] == 50
        assert updated.range_entries[0]["end_vendor_id"] == 55

    async def test_update_with_mixed_single_and_range_vendors(
        self,
        async_session: AsyncSession,
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test updating with a mix of single vendors and ranges."""
        update_data = {
            "range_entries": [
                {"start_vendor_id": 1, "end_vendor_id": 5},
                {"start_vendor_id": 8},  # Single vendor
                {"start_vendor_id": 15, "end_vendor_id": 20},
            ],
        }
        updated = await existing_restriction_allow_specific_vendors.update_async(
            async_db=async_session, data=update_data
        )
        assert len(updated.range_entries) == 3
        assert updated.range_entries[0]["start_vendor_id"] == 1
        assert updated.range_entries[0]["end_vendor_id"] == 5
        assert updated.range_entries[1]["start_vendor_id"] == 8
        assert updated.range_entries[1]["end_vendor_id"] is None
        assert updated.range_entries[2]["start_vendor_id"] == 15
        assert updated.range_entries[2]["end_vendor_id"] == 20

    async def test_update_with_consecutive_ranges(
        self,
        async_session: AsyncSession,
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test updating with consecutive ranges."""
        update_data = {
            "range_entries": [
                {"start_vendor_id": 1, "end_vendor_id": 5},
                {
                    "start_vendor_id": 6,
                    "end_vendor_id": 10,
                },  # Consecutive with first range
                {
                    "start_vendor_id": 11,
                    "end_vendor_id": 15,
                },  # Consecutive with second range
            ],
        }
        updated = await existing_restriction_allow_specific_vendors.update_async(
            async_db=async_session, data=update_data
        )
        assert len(updated.range_entries) == 3
        assert updated.range_entries[0]["start_vendor_id"] == 1
        assert updated.range_entries[0]["end_vendor_id"] == 5
        assert updated.range_entries[1]["start_vendor_id"] == 6
        assert updated.range_entries[1]["end_vendor_id"] == 10
        assert updated.range_entries[2]["start_vendor_id"] == 11
        assert updated.range_entries[2]["end_vendor_id"] == 15

    async def test_update_with_max_vendor_id_range(
        self,
        async_session: AsyncSession,
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test updating with a range that extends to MAX_GVL_ID."""
        update_data = {
            "range_entries": [
                {
                    "start_vendor_id": 9995,
                    "end_vendor_id": 9999,
                },  # Range up to MAX_GVL_ID
            ],
        }
        updated = await existing_restriction_allow_specific_vendors.update_async(
            async_db=async_session, data=update_data
        )
        assert len(updated.range_entries) == 1
        assert updated.range_entries[0]["start_vendor_id"] == 9995
        assert updated.range_entries[0]["end_vendor_id"] == 9999

    async def test_update_overlapping_allow_and_restrict_vendors(
        self,
        async_session: AsyncSession,
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test that updating a restriction to overlap with transformed allowlist ranges fails."""
        # Create another restriction for the same purpose with restrict_specific_vendors
        other_data = {
            "tcf_configuration_id": existing_restriction_allow_specific_vendors.tcf_configuration_id,
            "purpose_id": existing_restriction_allow_specific_vendors.purpose_id,
            "restriction_type": TCFRestrictionType.require_legitimate_interest,  # Different type
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 2, "end_vendor_id": 4},  # Non-overlapping range
            ],
        }
        other_restriction = await TCFPublisherRestriction.create_async(
            async_db=async_session, data=other_data
        )

        # Try to update the new restriction with ranges that would overlap with the transformed ranges
        # of the existing restriction
        # The existing restriction allows vendors 1-5 and 7-10, so the transformed ranges are 6, 11-9999
        update_data = {
            "range_entries": [
                {
                    "start_vendor_id": 6,
                    "end_vendor_id": 10,
                },  # Overlaps with transformed ranges
            ],
        }
        with pytest.raises(ValueError, match="Overlapping ranges found"):
            await other_restriction.update_async(
                async_db=async_session, data=update_data
            )

        # Cleanup
        await async_session.delete(other_restriction)
        await async_session.commit()

    async def test_update_non_overlapping_mixed_vendor_restrictions(
        self,
        async_session: AsyncSession,
        existing_restriction_allow_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test that updating a restriction with non-overlapping ranges succeeds."""
        # Create another restriction for the same purpose with restrict_specific_vendors
        other_data = {
            "tcf_configuration_id": existing_restriction_allow_specific_vendors.tcf_configuration_id,
            "purpose_id": existing_restriction_allow_specific_vendors.purpose_id,
            "restriction_type": TCFRestrictionType.require_legitimate_interest,  # Different type
            "vendor_restriction": TCFVendorRestriction.restrict_specific_vendors,
            "range_entries": [
                {"start_vendor_id": 2, "end_vendor_id": 4},  # Non-overlapping range
            ],
        }
        other_restriction = await TCFPublisherRestriction.create_async(
            async_db=async_session, data=other_data
        )

        # Update the first restriction with ranges that don't overlap with any other ranges
        # The existing restriction allows vendors 1-5
        # The other restriction restricts vendors 2-4
        update_data = {
            "range_entries": [
                {"start_vendor_id": 1, "end_vendor_id": 5},  # Allowed vendors
                {"start_vendor_id": 7},  # Single vendor within allowed range
            ],
        }
        updated = await other_restriction.update_async(
            async_db=async_session, data=update_data
        )

        assert updated is not None
        assert len(updated.range_entries) == 2
        assert updated.range_entries[0]["start_vendor_id"] == 1
        assert updated.range_entries[0]["end_vendor_id"] == 5
        assert updated.range_entries[1]["start_vendor_id"] == 7
        assert updated.range_entries[1]["end_vendor_id"] is None

        # Cleanup
        await async_session.delete(other_restriction)
        await async_session.commit()

    async def test_update_restrict_specific_vendors_no_entries(
        self,
        async_session: AsyncSession,
        existing_restriction_restrict_specific_vendors: TCFPublisherRestriction,
    ) -> None:
        """Test that updating a restrict_specific_vendors restriction to have no range entries fails."""
        update_data = {
            "range_entries": [],  # Empty range entries
        }
        with pytest.raises(
            ValueError,
            match="A restrict_specific_vendors restriction must have at least one range entry",
        ):
            await existing_restriction_restrict_specific_vendors.update_async(
                async_db=async_session, data=update_data
            )


class TestTransformAllowListRestrictions:
    """Test cases for the transform_allowlist_restriction method."""

    def test_single_vendor_range(self) -> None:
        """Test transforming a single vendor range."""
        entries = [RangeEntry(start_vendor_id=5)]  # Single vendor at 5
        transformed = TCFPublisherRestriction.transform_allowlist_restriction(entries)

        assert len(transformed) == 2
        assert transformed[0].start_vendor_id == 1
        assert transformed[0].end_vendor_id == 4  # Up to but not including 5
        assert transformed[1].start_vendor_id == 6
        assert transformed[1].end_vendor_id == 9999  # Up to MAX_GVL_ID

    def test_vendor_range_covers_all_vendors(self) -> None:
        """Test transforming a single vendor range that covers all vendors."""
        entries = [RangeEntry(start_vendor_id=1, end_vendor_id=9999)]
        transformed = TCFPublisherRestriction.transform_allowlist_restriction(entries)

        assert len(transformed) == 0

    def test_single_vendor_range_starts_at_one(self) -> None:
        """Test transforming a single vendor range that starts at vendor ID 1."""
        entries = [RangeEntry(start_vendor_id=1)]
        transformed = TCFPublisherRestriction.transform_allowlist_restriction(entries)

        assert len(transformed) == 1
        assert transformed[0].start_vendor_id == 2
        assert transformed[0].end_vendor_id == 9999

    def test_single_vendor_range_ends_at_max(self) -> None:
        """Test transforming a single vendor range that ends at MAX_GVL_ID."""
        entries = [RangeEntry(start_vendor_id=9999)]
        transformed = TCFPublisherRestriction.transform_allowlist_restriction(entries)

        assert len(transformed) == 1
        assert transformed[0].start_vendor_id == 1
        assert transformed[0].end_vendor_id == 9998

    def test_multiple_ranges(self) -> None:
        """Test transforming multiple ranges."""
        entries = [
            RangeEntry(start_vendor_id=5, end_vendor_id=10),
            RangeEntry(start_vendor_id=25, end_vendor_id=40),
            RangeEntry(start_vendor_id=123),
            RangeEntry(start_vendor_id=345, end_vendor_id=380),
        ]
        transformed = TCFPublisherRestriction.transform_allowlist_restriction(entries)

        assert len(transformed) == 5
        # 1-4 (before first range)
        assert transformed[0].start_vendor_id == 1
        assert transformed[0].end_vendor_id == 4
        # 11-24 (between ranges)
        assert transformed[1].start_vendor_id == 11
        assert transformed[1].end_vendor_id == 24
        # 41-122 (between ranges)
        assert transformed[2].start_vendor_id == 41
        assert transformed[2].end_vendor_id == 122
        # 124-344 (between ranges)
        assert transformed[3].start_vendor_id == 124
        assert transformed[3].end_vendor_id == 344
        # 381-9999 (after last range)
        assert transformed[4].start_vendor_id == 381
        assert transformed[4].end_vendor_id == 9999

    def test_mixed_single_and_range_vendors(self) -> None:
        """Test transforming a mix of single vendors and ranges."""
        entries = [
            RangeEntry(start_vendor_id=5, end_vendor_id=10),
            RangeEntry(start_vendor_id=15),  # Single vendor
            RangeEntry(start_vendor_id=25, end_vendor_id=30),
        ]
        transformed = TCFPublisherRestriction.transform_allowlist_restriction(entries)

        assert len(transformed) == 4
        # 1-4 (before first range)
        assert transformed[0].start_vendor_id == 1
        assert transformed[0].end_vendor_id == 4
        # 11-14 (between first range and single vendor)
        assert transformed[1].start_vendor_id == 11
        assert transformed[1].end_vendor_id == 14
        # 16-24 (between single vendor and last range)
        assert transformed[2].start_vendor_id == 16
        assert transformed[2].end_vendor_id == 24
        # 31-9999 (after last range)
        assert transformed[3].start_vendor_id == 31
        assert transformed[3].end_vendor_id == 9999

    def test_ranges_starting_at_one(self) -> None:
        """Test transforming ranges that start at vendor ID 1."""
        entries = [
            RangeEntry(start_vendor_id=1, end_vendor_id=5),
            RangeEntry(start_vendor_id=10, end_vendor_id=15),
        ]
        transformed = TCFPublisherRestriction.transform_allowlist_restriction(entries)

        assert len(transformed) == 2
        # 6-9 (between ranges)
        assert transformed[0].start_vendor_id == 6
        assert transformed[0].end_vendor_id == 9
        # 16-9999 (after last range)
        assert transformed[1].start_vendor_id == 16
        assert transformed[1].end_vendor_id == 9999

    def test_consecutive_range_with_edges(self) -> None:
        """Test transforming consecutive ranges."""
        entries = [
            RangeEntry(start_vendor_id=1, end_vendor_id=5),
            RangeEntry(start_vendor_id=6, end_vendor_id=15),
            RangeEntry(start_vendor_id=16, end_vendor_id=20),
            RangeEntry(start_vendor_id=200, end_vendor_id=250),
            RangeEntry(start_vendor_id=251, end_vendor_id=300),
            RangeEntry(start_vendor_id=9950, end_vendor_id=9980),
            RangeEntry(start_vendor_id=9981, end_vendor_id=9999),
        ]
        transformed = TCFPublisherRestriction.transform_allowlist_restriction(entries)

        assert len(transformed) == 2
        # 21-199 (between ranges)
        assert transformed[0].start_vendor_id == 21
        assert transformed[0].end_vendor_id == 199
        # 301-9949 (between ranges)
        assert transformed[1].start_vendor_id == 301
        assert transformed[1].end_vendor_id == 9949

    def test_consecutive_ranges_with_single_vendors(self) -> None:
        """Test transforming consecutive ranges with single vendors."""
        entries = [
            RangeEntry(start_vendor_id=7, end_vendor_id=10),
            RangeEntry(start_vendor_id=11, end_vendor_id=20),
            RangeEntry(start_vendor_id=21),
            RangeEntry(start_vendor_id=22, end_vendor_id=25),
            RangeEntry(start_vendor_id=26),
        ]
        transformed = TCFPublisherRestriction.transform_allowlist_restriction(entries)

        assert len(transformed) == 2
        # 1-6 (before first range)
        assert transformed[0].start_vendor_id == 1
        assert transformed[0].end_vendor_id == 6
        # 27-9999 (after last range)
        assert transformed[1].start_vendor_id == 27
        assert transformed[1].end_vendor_id == 9999

    def test_ranges_ending_at_max(self) -> None:
        """Test transforming ranges that end at MAX_GVL_ID."""
        entries = [
            RangeEntry(start_vendor_id=5, end_vendor_id=10),
            RangeEntry(start_vendor_id=100, end_vendor_id=9999),
        ]
        transformed = TCFPublisherRestriction.transform_allowlist_restriction(entries)

        assert len(transformed) == 2
        # 1-4 (before first range)
        assert transformed[0].start_vendor_id == 1
        assert transformed[0].end_vendor_id == 4
        # 11-99 (between ranges)
        assert transformed[1].start_vendor_id == 11
        assert transformed[1].end_vendor_id == 99

    def test_empty_entries_raises_error(self) -> None:
        """Test that empty entries raise a ValueError."""
        with pytest.raises(ValueError, match="No range entries found"):
            TCFPublisherRestriction.transform_allowlist_restriction([])
