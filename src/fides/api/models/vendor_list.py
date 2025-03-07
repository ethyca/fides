from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import TIMESTAMP, Column, DateTime, String

from fides.api.db.base_class import Base


class VendorList(Base):
    """
    Raw JSON storage of the GVL Vendor List in DB
    """

    __tablename__ = "vendor_list"

    json_raw = Column(JSONB, nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    version = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<VendorList {self.version}>"
