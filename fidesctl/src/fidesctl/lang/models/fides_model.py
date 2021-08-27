import re
from typing import Optional

from pydantic import BaseModel, Field
from pydantic.types import ConstrainedStr, constr


class FidesKey(ConstrainedStr):
    """
    A FidesKey should only contain alphanumeric characters or '_'
    """

    regex = re.compile(r"^[\w]+$")


class FidesModel(BaseModel):
    """The base model for all Fides Resources."""

    id: Optional[int]
    fidesKey: FidesKey
