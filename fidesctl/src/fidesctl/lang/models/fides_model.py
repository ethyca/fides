from typing import Optional

from pydantic import BaseModel


class FidesModel(BaseModel):
    """The base model for all Fides Resources."""

    id: Optional[int]
    fidesKey: str
