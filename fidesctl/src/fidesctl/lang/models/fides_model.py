from pydantic import BaseModel


class FidesModel(BaseModel):
    """The base model for all Fides Resources."""

    fidesKey: str
