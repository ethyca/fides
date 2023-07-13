from sqlalchemy import Column, String, Boolean

from fides.api.db.base_class import Base
from fides.api.db.util import EnumColumn
from fides.api.models.privacy_notice import ConsentMechanism, EnforcementLevel


class TCFDataUse(Base):
    """
    Table to store TCF Data Use Information
    """

    name = Column(String, nullable=False)
    key = Column(String, nullable=False)
    consent_mechanism = Column(EnumColumn(ConsentMechanism), nullable=True)
    enforcement_level = Column(EnumColumn(EnforcementLevel), nullable=True)
    has_gpc_flag = Column(Boolean, nullable=True, default=False)
    notice_key = Column(String, nullable=True)
