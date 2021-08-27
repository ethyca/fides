from typing import List, Optional

from pydantic import BaseModel

from fidesctl.lang.models.fides_model import FidesModel


class Organization(BaseModel):
    id: Optional[int]
    fidesKey: str
    name: str
    description: str
