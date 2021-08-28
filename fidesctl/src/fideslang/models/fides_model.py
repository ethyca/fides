from typing import Optional

from pydantic import BaseModel

from fideslang.models.validation import FidesKey


class FidesModel(BaseModel):
    """The base model for all Fides Resources."""

    id: Optional[int]
    organizationId: int = 1
    name: str
    description: Optional[str]
    fidesKey: FidesKey
