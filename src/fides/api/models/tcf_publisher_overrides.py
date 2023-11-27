from sqlalchemy import Boolean, Column, Integer, String

from fides.api.db.base_class import Base


class TCFPublisherOverrides(Base):
    """
    Stores TCF Publisher Overrides
    """

    purpose = Column(Integer, nullable=False)
    is_included = Column(Boolean, server_default="t", default=True)
    required_legal_basis = Column(String)
