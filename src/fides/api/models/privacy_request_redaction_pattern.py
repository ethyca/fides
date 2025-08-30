from typing import List, Set

from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


class PrivacyRequestRedactionPattern(Base):
    """
    Stores one regex pattern per row for masking dataset, collection, and field names
    in DSR package reports.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "privacy_request_redaction_pattern"

    # One pattern per row; unique to prevent duplicates
    pattern = Column(String, nullable=False, unique=True)

    @classmethod
    def get_patterns(cls, db: Session) -> List[str]:
        """
        Get the current list of masking patterns ordered by creation time.

        Returns:
            List of regex pattern strings, or None if no patterns are configured
        """
        rows = db.query(cls).order_by(cls.created_at.asc()).all()
        if not rows:
            return []
        return [row.pattern for row in rows]

    @classmethod
    def replace_patterns(cls, db: Session, patterns: List[str]) -> List[str]:
        """
        Replace the set of stored patterns with the provided list using set reconciliation.

        - Adds patterns that are not present
        - Removes patterns that are no longer desired
        - Returns the resulting canonical list in deterministic order
        """
        # Normalize: trim whitespace, remove empties and duplicates
        desired: Set[str] = {p.strip() for p in patterns if p and p.strip()}

        # Fetch existing patterns from DB as a set
        existing: Set[str] = set(p for (p,) in db.query(cls.pattern).all())

        to_add = desired - existing
        to_remove = existing - desired

        if to_remove:
            db.query(cls).filter(cls.pattern.in_(list(to_remove))).delete(
                synchronize_session=False
            )

        if to_add:
            db.bulk_save_objects([cls(pattern=p) for p in to_add])

        db.commit()

        return sorted(desired)
