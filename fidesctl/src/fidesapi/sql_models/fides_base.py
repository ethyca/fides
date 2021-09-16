from sqlalchemy import Column, Integer, String


class FidesBase:
    """The base SQL model for all Fides Resources."""

    id = Column(Integer, primary_key=True, index=True)
    fidesKey = Column(String, primary_key=True, index=True)
    organization_fides_key = Column(String)
    name = Column(String)
    description = Column(String)
