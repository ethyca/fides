from sqlalchemy import Boolean, Column, String
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base


class CustomConnectorTemplate(Base):
    """A model representing a custom connector template"""

    @declared_attr
    def __tablename__(self) -> str:
        return "custom_connector_template"

    key = Column(String, index=True, unique=True, nullable=False)
    name = Column(String, index=False, unique=False, nullable=False)
    config = Column(String, index=False, unique=False, nullable=False)
    dataset = Column(String, index=False, unique=False, nullable=False)
    icon = Column(String, index=False, unique=False, nullable=True)
    functions = Column(String, index=False, unique=False, nullable=True)
    # indicates that this custom connector template should be replaced
    # if a newer version is available from other sources
    replaceable = Column(
        Boolean, index=False, unique=False, nullable=False, default=False
    )
