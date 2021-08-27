import re
from typing import Optional

from pydantic import BaseModel
from pydantic.types import ConstrainedStr


class FidesKey(ConstrainedStr):
    """
    A FidesKey should only contain alphanumeric characters or '_'
    """

    regex = re.compile(r"^[\w]+$")


class FidesModel(BaseModel):
    """The base model for all Fides Resources."""

    id: Optional[int]
    organizationId: int = 1
    name: str
    description: Optional[str]
    fidesKey: FidesKey
