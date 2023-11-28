from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import declared_attr

from fides.api.db.base_class import Base


class TCFPublisherOverride(Base):
    """
    Stores TCF Publisher Overrides
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "tcf_publisher_overrides"

    purpose = Column(Integer, nullable=False)
    is_included = Column(Boolean, server_default="t", default=True)
    required_legal_basis = Column(String)
