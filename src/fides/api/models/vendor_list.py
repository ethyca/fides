from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, String

from fides.api.db.base_class import Base


class VendorList(Base):
    """
    Raw JSON storage of the GVL Vendor List in DB
    """

    __tablename__ = "vendor_list"

    json_raw = Column(JSONB, nullable=True)
    version = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<VendorList {self.version}>"

    def upsert(self, session) -> None:
        """
        Upsert the vendor list into the database.
        """
        # self.updated_at =
        session.merge(self)
        session.commit()
        session.refresh(self)
        return self
