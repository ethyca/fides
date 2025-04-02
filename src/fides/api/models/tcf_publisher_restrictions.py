from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field, ValidationError, model_validator
from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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
    end_vendor_id: int | None = Field(
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
    def create(
        cls,
        db: Session,
        *,
        data: Dict[str, Any],
        check_name: bool = True,
    ) -> "TCFPublisherRestriction":
        """
        Create a new TCFPublisherRestriction with validated range_entries.
        Validates each range entry using the RangeEntry Pydantic model.
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

        return super().create(db=db, data=data, check_name=check_name)
