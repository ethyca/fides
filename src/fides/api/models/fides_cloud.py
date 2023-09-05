from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

from fides.api.db.base_class import Base


class FidesCloud(Base):
    """Stores all Fides Cloud related config variables"""

    config = Column(MutableDict.as_mutable(JSONB), nullable=True)
