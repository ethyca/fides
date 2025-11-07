from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base


class SaasTemplateDataset(Base):
    """
    Stores the latest template dataset for each SaaS connection type.

    This table maintains a record of the template datasets that come with
    Fides for each SaaS connector type. It's used as a baseline for
    detecting customer modifications to datasets.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "saas_template_dataset"

    connection_type = Column(String, nullable=False, unique=True, index=True)
    dataset_json = Column(JSONB, nullable=False)

    def __repr__(self) -> str:
        return f"<SaasTemplateDataset(connection_type='{self.connection_type}')>"
