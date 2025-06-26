from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, model_validator
from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Index, Integer, String, insert, select, update
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base, FidesBase

if TYPE_CHECKING:
    from fides.api.models.privacy_experience import PrivacyExperienceConfig


class TCFRestrictionType(str, Enum):
    """Enum for TCF restriction types"""

    purpose_restriction = "purpose_restriction"
    require_consent = "require_consent"
    require_legitimate_interest = "require_legitimate_interest"


class TCFVendorRestriction(str, Enum):
    """Enum for TCF vendor restriction types"""

    restrict_all_vendors = "restrict_all_vendors"
    allow_specific_vendors = "allow_specific_vendors"
    restrict_specific_vendors = "restrict_specific_vendors"


# This is Pydantic model used for validation, not a database model!
class RangeEntry(BaseModel):
    """
    Pydantic model that represents a vendor range entry as per the TCF spec,
    used for Publisher Restrictions.
    A range entry must have a start_vendor_id and optionally an end_vendor_id.
    If end_vendor_id is present, it must be greater than start_vendor_id.
    """

    start_vendor_id: int = Field(description="The starting vendor ID in the range")
    end_vendor_id: Optional[int] = Field(
        default=None, description="The ending vendor ID in the range (inclusive)"
    )

    @model_validator(mode="after")
    def validate_vendor_range(self) -> "RangeEntry":
        """Validates that end_vendor_id is greater than start_vendor_id if present."""
        if self.end_vendor_id is not None and self.end_vendor_id < self.start_vendor_id:
            raise ValueError(
                "end_vendor_id must be greater than or equal to start_vendor_id"
            )
        return self

    @property
    def effective_end_vendor_id(self) -> int:
        """Get the effective end of the range."""
        return self.end_vendor_id or self.start_vendor_id

    def overlaps_with(self, other: "RangeEntry") -> bool:
        """
        Check if this range overlaps with another range.
        Two ranges overlap if the end of the range that starts first is greater than
        or equal to the start of the range that starts second.
        """
        # Sort ranges by start_vendor_id
        first = self if self.start_vendor_id <= other.start_vendor_id else other
        second = other if self.start_vendor_id <= other.start_vendor_id else self

        # If first range's end is >= second range's start, they overlap
        return first.effective_end_vendor_id >= second.start_vendor_id


class TCFConfiguration(Base):
    """
    Stores TCF Configuration settings.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "tcf_configuration"

    # redefined here because there's a minor, unintended discrepancy between
    # this `id` field and that of the `Base` class, which explicitly sets `index=True`.
    # TODO: we likely should _not_ be setting `index=True` on the `id`
    # attribute of the `Base` class, as `primary_key=True` already specifies a
    # primary key constraint, which will implicitly create an index for the field.
    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)
    name = Column(String, nullable=False, unique=True)

    privacy_experience_configs = relationship(
        "PrivacyExperienceConfig",
        back_populates="tcf_configuration",
        lazy="selectin",
        viewonly=True,
    )


class TCFPublisherRestriction(Base):
    """
    Stores TCF Publisher Restrictions. TCF Publisher Restrictions belong to a TCF Configuration,
    and specify the restriction type and vendor restriction for a given purpose.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "tcf_publisher_restriction"

    # redefined here because there's a minor, unintended discrepancy between
    # this `id` field and that of the `Base` class, which explicitly sets `index=True`.
    # TODO: we likely should _not_ be setting `index=True` on the `id`
    # attribute of the `Base` class, as `primary_key=True` already specifies a
    # primary key constraint, which will implicitly create an index for the field.
    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)

    tcf_configuration_id = Column(
        String(255),
        ForeignKey("tcf_configuration.id", ondelete="CASCADE"),
        nullable=False,
    )
    purpose_id = Column(Integer, nullable=False)
    restriction_type = Column(EnumColumn(TCFRestrictionType), nullable=False)
    vendor_restriction = Column(EnumColumn(TCFVendorRestriction), nullable=False)

    # range_entries represents a list of RangeEntry objects as per the TCF spec.
    # A RangeEntry object will have a start_vendor_id and an end_vendor_id (the
    # end vendor id is included in the range).
    # If the range represents a single vendor, then the end_vendor_id can be omitted.
    # TCF spec also includes an IsARange boolean, which we are omitting because it
    # can be inferred from the presence of the end_vendor_id.
    range_entries = Column(
        ARRAY(JSONB),
        nullable=False,
        server_default="{}",
        default=list,
    )

    __table_args__ = (
        Index(
            "ix_tcf_publisher_restriction_config_purpose",
            "tcf_configuration_id",
            "purpose_id",
        ),
    )

    def __init__(self, **kwargs: Any) -> None:
        validated_kwargs = self.validate_publisher_restriction_data(kwargs)
        super().__init__(**validated_kwargs)

    @staticmethod
    def validate_entires_for_vendor_restriction(
        entries: List[RangeEntry], vendor_restriction: TCFVendorRestriction
    ) -> None:
        """
        Validates that if vendor_restriction is restrict_all_vendors, then the entries list is empty.
        If vendor_restriction is not restrict_all_vendors, then there must be at least one entry.
        """
        if vendor_restriction == TCFVendorRestriction.restrict_all_vendors and entries:
            raise ValueError(
                "A restrict_all_vendors restriction cannot have any range entries"
            )

        if (
            vendor_restriction != TCFVendorRestriction.restrict_all_vendors
            and not entries
        ):
            raise ValueError(
                f"A {vendor_restriction} restriction must have at least one range entry"
            )

    @staticmethod
    def check_for_overlaps(entries: List[RangeEntry]) -> None:
        """
        Check for overlapping ranges in a list of RangeEntry objects,
        raises a ValueError if any pair of RangeEntry overlaps with each other.
        Sorts the ranges by start_vendor_id and compares adjacent ranges.
        """
        # Sort ranges by start_vendor_id
        sorted_entries = sorted(entries, key=lambda x: x.start_vendor_id)

        # Compare each range with the next one
        for i in range(len(sorted_entries) - 1):
            current = sorted_entries[i]
            next_entry = sorted_entries[i + 1]
            if current.overlaps_with(next_entry):
                raise ValueError(
                    f"Overlapping ranges found: {current.model_dump()} overlaps with {next_entry.model_dump()}"
                )

    @classmethod
    def validate_publisher_restriction_data(
        cls, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate the restriction data.
        """
        raw_range_entries = data.get("range_entries", [])

        try:
            # Validate each range entry using the Pydantic model
            validated_entries = [
                RangeEntry.model_validate(entry) for entry in raw_range_entries
            ]
        except ValidationError as e:
            raise ValueError(f"Invalid range entry: {str(e)}")

        # Validate the entries for the vendor restriction
        cls.validate_entires_for_vendor_restriction(
            validated_entries, data["vendor_restriction"]
        )
        # Check for overlapping ranges
        cls.check_for_overlaps(validated_entries)

        data["range_entries"] = [entry.model_dump() for entry in validated_entries]

        return data

    @classmethod
    async def check_for_restriction_conflicts(
        cls,
        *,
        async_db: AsyncSession,
        configuration_id: str,
        purpose_id: int,
        restriction_type: TCFRestrictionType,
        vendor_restriction: TCFVendorRestriction,
        range_entries: Optional[list[RangeEntry]] = None,
        restriction_id: Optional[str] = None,
    ) -> None:
        """
        Checks that the new restriction data does not conflict with any existing restrictions for the purpose.
        """
        # First, get all the restrictions for the purpose in the given configuration
        query = (
            select(cls)  # type: ignore[arg-type]
            .where(cls.tcf_configuration_id == configuration_id)
            .where(cls.purpose_id == purpose_id)
        )
        # If we're updating an existing restriction, exclude it from the list of
        # restrictions so it doesn't conflict with itself
        if restriction_id:
            query = query.where(cls.id != restriction_id)

        restrictions_result = await async_db.execute(query)
        relevant_restrictions = restrictions_result.scalars().all()

        if any(
            restriction.vendor_restriction == TCFVendorRestriction.restrict_all_vendors
            for restriction in relevant_restrictions
        ):
            raise ValueError(
                f"Invalid restriction for purpose {purpose_id}: a restrict_all_vendors restriction exists for this purpose."
            )

        # If we're creating a restrict_all_vendors restriction,
        # then there should be no other restrictions for this purpose
        if vendor_restriction == TCFVendorRestriction.restrict_all_vendors:
            if relevant_restrictions:
                raise ValueError(
                    f"Invalid restrict_all_vendors restriction for purpose {purpose_id}: other restrictions already exist for this purpose."
                )

            return None

        # If we already have a restriction for that restriction type,
        # then we raise an error
        if any(
            restriction.restriction_type == restriction_type
            for restriction in relevant_restrictions
        ):
            raise ValueError(
                f"Invalid {restriction_type} restriction for purpose {purpose_id}: a restriction of this type already exists for this purpose."
            )

        # We now need to check for vendor overlaps between all the restrictions.
        # To achieve this, we need to transform allowlist-style restrictions into
        # actual restriction ranges (rather than "allow" ranges).
        new_range_entries = (
            cls.transform_allowlist_restriction(range_entries or [])
            if vendor_restriction == TCFVendorRestriction.allow_specific_vendors
            else (range_entries or [])
        )

        existing_range_entries = []
        for restriction in relevant_restrictions:
            range_entries = [
                RangeEntry.model_validate(entry) for entry in restriction.range_entries
            ]
            transformed_range_entries = (
                cls.transform_allowlist_restriction(range_entries)
                if restriction.vendor_restriction
                == TCFVendorRestriction.allow_specific_vendors
                else range_entries
            )
            existing_range_entries.extend(transformed_range_entries)

        all_entries = [*existing_range_entries, *new_range_entries]
        cls.check_for_overlaps(all_entries)

    @classmethod
    def transform_allowlist_restriction(
        cls, range_entries: list[RangeEntry]
    ) -> list[RangeEntry]:
        """
        Transform allowlist-style restrictions into restriction ranges.
        E.g if you have an "allow specific vendors" restriction with the range_entries
        [
            {start_vendor_id: 5, end_vendor_id: 10},
            {start_vendor_id: 25, end_vendor_id: 40},
            {start_vendor_id: 123 },
            {start_vendor_id: 345, end_vendor_id: 380},
        ],
        the transformed restriction ranges would be:
        [
            {start_vendor_id: 1, end_vendor_id: 4},
            {start_vendor_id: 11, end_vendor_id: 24},
            {start_vendor_id: 41, end_vendor_id: 122},
            {start_vendor_id: 124, end_vendor_id: MAX_GVL_ID},
        ]
        """
        MAX_GVL_ID = 9999  # TODO: get this from the TCF spec

        # First, we need to sort the range_entries by start_vendor_id
        sorted_range_entries = sorted(range_entries, key=lambda x: x.start_vendor_id)

        # Now, we need to transform the allowlist-style restrictions into
        # actual restriction ranges.
        transformed_range_entries: list[RangeEntry] = []

        total_entries = len(sorted_range_entries)

        # This shouldn't happen, but just in case
        if total_entries == 0:
            raise ValueError(
                "No range entries found for allow_specific_vendors restriction"
            )

        # If the first range entry starts at a number greater than 1,
        # we need to add a transformed range entry from 1 up to the entry's start
        if sorted_range_entries[0].start_vendor_id > 1:
            transformed_range_entries.append(
                RangeEntry(
                    start_vendor_id=1,
                    end_vendor_id=sorted_range_entries[0].start_vendor_id - 1,
                )
            )

        # Iterate through the sorted range_entries and transform them into restriction ranges
        for idx, range_entry in enumerate(sorted_range_entries):
            # For all but the last range entry, we add an entry that corresponds to the numbers
            # between the end of the current range entry and the start of the next range entry
            if idx < total_entries - 1:
                # Only create a range entry if there's actually a gap between the ranges
                next_start = sorted_range_entries[idx + 1].start_vendor_id
                current_end = range_entry.effective_end_vendor_id
                if next_start > current_end + 1:
                    transformed_range_entries.append(
                        RangeEntry(
                            start_vendor_id=current_end + 1,
                            end_vendor_id=next_start - 1,
                        )
                    )

        # If the last range entry ends at a number less than MAX_GVL_ID,
        # we need to add a transformed range entry from the last entry's end to MAX_GVL_ID
        if sorted_range_entries[-1].effective_end_vendor_id < MAX_GVL_ID:
            transformed_range_entries.append(
                RangeEntry(
                    start_vendor_id=sorted_range_entries[-1].effective_end_vendor_id
                    + 1,
                    end_vendor_id=MAX_GVL_ID,
                )
            )

        # Return the transformed restriction entries
        return transformed_range_entries

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: Dict[str, Any],
        check_name: bool = True,
    ) -> "TCFPublisherRestriction":
        raise NotImplementedError("Use create_async instead")

    @classmethod
    async def create_async(
        cls,
        async_db: AsyncSession,
        *,
        data: Dict[str, Any],
    ) -> "TCFPublisherRestriction":
        """
        Create a new TCFPublisherRestriction with validated range_entries.
        """

        data = cls.validate_publisher_restriction_data(data)

        await cls.check_for_restriction_conflicts(
            async_db=async_db,
            configuration_id=data["tcf_configuration_id"],
            purpose_id=data["purpose_id"],
            restriction_type=TCFRestrictionType(data["restriction_type"]),
            vendor_restriction=TCFVendorRestriction(data["vendor_restriction"]),
            range_entries=[
                RangeEntry.model_validate(entry) for entry in data["range_entries"]
            ],
        )

        values = {
            "tcf_configuration_id": data["tcf_configuration_id"],
            "purpose_id": data["purpose_id"],
            "restriction_type": data["restriction_type"],
            "vendor_restriction": data["vendor_restriction"],
            "range_entries": data["range_entries"],
        }

        # Insert the new restriction
        insert_stmt = insert(cls).values(values)  # type: ignore[arg-type]
        result = await async_db.execute(insert_stmt)
        record_id = result.inserted_primary_key.id

        created_record = await async_db.execute(select(cls).where(cls.id == record_id))  # type: ignore[arg-type]
        return created_record.scalars().first()

    async def update_async(
        self, async_db: AsyncSession, data: Dict[str, Any]
    ) -> "TCFPublisherRestriction":
        """
        Update a TCFPublisherRestriction with the data.
        Validates the data and checks for vendor overlaps.
        """
        # Create a new dict merging the existing data and the updated data
        updated_data = {
            "id": self.id,
            "tcf_configuration_id": self.tcf_configuration_id,
            "purpose_id": self.purpose_id,
            "restriction_type": self.restriction_type,
            "vendor_restriction": self.vendor_restriction,
            "range_entries": self.range_entries,
            **data,
        }

        # First validate the data on its own
        data = self.validate_publisher_restriction_data(updated_data)

        # Then check for conflicts
        await self.check_for_restriction_conflicts(
            async_db=async_db,
            configuration_id=self.tcf_configuration_id,
            purpose_id=self.purpose_id,
            restriction_type=TCFRestrictionType(data["restriction_type"]),
            vendor_restriction=TCFVendorRestriction(data["vendor_restriction"]),
            range_entries=[
                RangeEntry.model_validate(entry) for entry in data["range_entries"]
            ],
            restriction_id=self.id,
        )

        # Remove the id from the updated
        updated_data.pop("id")

        # Finally, make the update
        update_query = (
            update(TCFPublisherRestriction)  # type: ignore[arg-type]
            .where(TCFPublisherRestriction.id == self.id)
            .values(**updated_data)
        )
        await async_db.execute(update_query)
        await async_db.commit()
        await async_db.refresh(self)

        return self
