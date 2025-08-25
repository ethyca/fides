from typing import Any, Dict, List, Optional

from sqlalchemy import ARRAY, Boolean, CheckConstraint, Column, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


class PrivacyRequestRedactionPatterns(Base):
    """
    A single-row table used to store regex patterns for masking dataset, collection,
    and field names in DSR package reports.

    This is a single-row table that stores an array of regex patterns that will be used
    to identify and mask sensitive names in privacy request package reports.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "privacy_request_redaction_patterns"

    patterns = Column(
        ARRAY(String),
        nullable=False,
        default=[],
    )  # Array of regex pattern strings

    single_row = Column(
        Boolean,
        default=True,
        nullable=False,
        unique=True,
    )  # used to constrain table to one row

    CheckConstraint(
        "single_row", name="privacy_request_redaction_patterns_single_row_check"
    )
    UniqueConstraint(
        "single_row", name="privacy_request_redaction_patterns_single_row_unique"
    )

    @classmethod
    def create_or_update(  # type: ignore[override]
        cls,
        db: Session,
        *,
        data: Dict[str, Any],
    ) -> "PrivacyRequestRedactionPatterns":
        """
        Creates the record if none exists, or updates the existing record.
        This effectively prevents more than a single record in the table.
        """
        existing_record = db.query(cls).first()
        if existing_record:
            return existing_record.update(db=db, data=data)

        return cls.create(db=db, data=data)

    @classmethod
    def get_patterns(cls, db: Session) -> Optional[List[str]]:
        """
        Get the current list of masking patterns.

        Returns:
            List of regex pattern strings, or None if no patterns are configured
        """
        record = db.query(cls).first()
        if record and record.patterns:
            return record.patterns
        return None

    def update(self, db: Session, data: Dict[str, Any]) -> "PrivacyRequestRedactionPatterns":  # type: ignore[override]
        """
        Updates the patterns record.

        Args:
            db: Database session
            data: Dictionary containing 'patterns' key with list of regex strings
        """
        if "patterns" in data:
            patterns = data["patterns"]
            if not isinstance(patterns, list):
                raise ValueError('"patterns" must be a list of strings')

            # Validate that all patterns are strings
            for pattern in patterns:
                if not isinstance(pattern, str):
                    raise ValueError("All patterns must be strings")

            self.patterns = patterns

        self.save(db=db)
        return self
