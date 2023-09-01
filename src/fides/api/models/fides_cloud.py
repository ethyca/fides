from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

from fides.api.db.base_class import Base


class FidesCloud(Base):
    """Stores all Fides Cloud related config variables"""

    config = Column(JSONB, nullable=True)
