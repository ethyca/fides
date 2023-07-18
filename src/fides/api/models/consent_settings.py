from sqlalchemy import Boolean, Column
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


class ConsentSettings(Base):
    """Organization-wide consent settings"""

    tcf_enabled = Column(Boolean)

    @classmethod
    def get_or_create(cls, db: Session) -> "ConsentSettings":
        consent_settings = db.query(ConsentSettings).first()
        if not consent_settings:
            ConsentSettings.create(db=db, data={"tcf_enabled": False})
        return consent_settings
