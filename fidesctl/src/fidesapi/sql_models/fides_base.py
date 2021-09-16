from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects import mysql


class FidesBase:
    """The base SQL model for all Fides Resources."""

    id = Column(Integer, primary_key=True, index=True)
    fides_key = Column(mysql.VARCHAR(200), primary_key=True, index=True)
    organization_fides_key = Column(Text)
    name = Column(Text)
    description = Column(Text)
