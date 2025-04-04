from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, model_validator
from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Index, Integer, String, insert, select, update
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


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
        if (
            self.end_vendor_id is not None
            and self.end_vendor_id <= self.start_vendor_id
        ):
            raise ValueError("end_vendor_id must be greater than start_vendor_id")
        return self

    def get_end(self) -> int:
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
        return first.get_end() >= second.start_vendor_id


class TCFConfiguration(Base):
    """
    Stores TCF Configuration settings.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "tcf_configuration"

    name = Column(String, nullable=False, index=True, unique=True)


class TCFPublisherRestriction(Base):
    """
    Stores TCF Publisher Restrictions. TCF Publisher Restrictions belong to a TCF Configuration,
    and specify the restriction type and vendor restriction for a given purpose.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "tcf_publisher_restriction"

    tcf_configuration_id = Column(
        String(255),
        ForeignKey("tcf_configuration.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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
        nullable=True,
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
        """
        if vendor_restriction == TCFVendorRestriction.restrict_all_vendors and entries:
            raise ValueError("restrict_all_vendors cannot have any range entries")

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
    async def validate_vendor_overlaps_for_purpose(
        cls,
        async_db: AsyncSession,
        configuration_id: str,
        purpose_id: int,
        new_data: dict,
    ) -> None:
        """
        Validates that the new vendor ranges do not overlap with any existing vendor ranges for the purpose
        in the given configuration.
        Raises a ValueError if any vendor ranges overlap.
        """
        # First, get all the restrictions for the purpose in the given configuration
        query = (
            select(cls)  # type: ignore[arg-type]
            .where(cls.tcf_configuration_id == configuration_id)
            .where(cls.purpose_id == purpose_id)
        )
        restrictions = await async_db.execute(query)
        restrictions = restrictions.scalars().all()

        # If we have an existing id, we need to exclude the current restriction from the list of existing restrictions
        # so that the new_data restrictions don't overlap with themselves
        if "id" in new_data:
            existing_entries = [
                entry
                for r in restrictions
                for entry in r.range_entries
                if r.id != new_data["id"]
            ]
        else:
            existing_entries = [
                entry for r in restrictions for entry in r.range_entries
            ]

        all_entries = [*existing_entries, *new_data.get("range_entries", [])]
        cls.check_for_overlaps(
            [RangeEntry.model_validate(entry) for entry in all_entries]
        )

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

        values = {
            "tcf_configuration_id": data["tcf_configuration_id"],
            "purpose_id": data["purpose_id"],
            "restriction_type": data["restriction_type"],
            "vendor_restriction": data["vendor_restriction"],
            "range_entries": data["range_entries"],
        }

        # Validate that the new vendor ranges do not overlap with any existing vendor ranges for the purpose
        await cls.validate_vendor_overlaps_for_purpose(
            async_db=async_db,
            configuration_id=data["tcf_configuration_id"],
            purpose_id=data["purpose_id"],
            new_data=values,
        )

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
        # Validate the data on its own
        data = self.validate_publisher_restriction_data(data)

        # Validate that the new vendor ranges do not overlap with any existing vendor ranges for the purpose
        await self.validate_vendor_overlaps_for_purpose(
            async_db=async_db,
            configuration_id=self.tcf_configuration_id,
            purpose_id=self.purpose_id,
            new_data={**data, "id": self.id},  # Pass in id explicitly
        )

        # Finally, make the update
        update_query = (
            update(TCFPublisherRestriction)  # type: ignore[arg-type]
            .where(TCFPublisherRestriction.id == self.id)
            .values(**data)
        )
        await async_db.execute(update_query)
        await async_db.commit()
        await async_db.refresh(self)

        return self
