from sqlalchemy import Boolean, Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base


class TCFPurposeOverride(Base):
    """
    Stores TCF Purpose Overrides

    Allows a customer to override Fides-wide which Purposes show up in the TCF Experience, and
    specify a global legal basis for that Purpose.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "tcf_purpose_overrides"

    purpose = Column(Integer, nullable=False, index=True)
    is_included = Column(Boolean, server_default="t", default=True)
    required_legal_basis = Column(String)

    __table_args__ = (UniqueConstraint("purpose"),)
