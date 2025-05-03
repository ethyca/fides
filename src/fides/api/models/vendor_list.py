from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, String
from sqlalchemy.orm import Session

from fides.api.db.base_class import OrmWrappedFidesBase


class VendorList(OrmWrappedFidesBase):
    """
    Raw JSON storage of the GVL Vendor List in DB
    """

    __tablename__ = "vendor_list"

    json_raw = Column(JSONB, nullable=True)
    version = Column(String, nullable=True)

    def upsert(self, db: Session) -> "VendorList":
        """
        Upsert the vendor list into the database.
        """
        db.merge(self)
        db.commit()
        return self
