from sqlalchemy import Boolean, Column
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


class ConsentSettings(Base):
    """Organization-wide consent settings"""

    tcf_enabled = Column(Boolean, default=False)

    @classmethod
    def get_or_create_with_defaults(cls, db: Session) -> "ConsentSettings":
        """We only have one organization-wide ConsentSettings record - fetch this if it
        exists, or create it and return if not.
        """
        consent_settings = db.query(ConsentSettings).first()
        if not consent_settings:
            return ConsentSettings.create(db=db, data={"tcf_enabled": False})  # type: ignore[attr-defined]
        return consent_settings
