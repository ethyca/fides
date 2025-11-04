from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB

from fides.api.db.base_class import Base


class SaasOfficialDataset(Base):
    """
    Stores the latest official dataset for each SaaS connection type.

    This table maintains a record of the official datasets that come with
    Fides for each SaaS connector type. It's used as a baseline for
    detecting customer modifications to datasets.
    """

    connection_type = Column(String, nullable=False, unique=True, index=True)
    dataset_json = Column(JSONB, nullable=False)

    def __repr__(self) -> str:
        return f"<SaasOfficialDataset(connection_type='{self.connection_type}')>"
