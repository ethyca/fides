from sqlalchemy import Boolean, Column
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


class ConsentSettings(Base):
    """Organization-wide consent settings"""

    tcf_enabled = Column(Boolean)

    @classmethod
    def get_or_create(cls, db: Session) -> "ConsentSettings":
        """We only have one organization-wide ConsentSettings record - fetch this if it
        exists, or create it and return if not.
        """
        consent_settings = db.query(ConsentSettings).first()
        if not consent_settings:
            return ConsentSettings.create(db=db, data={"tcf_enabled": False})
        return consent_settings
