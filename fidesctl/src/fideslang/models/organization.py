from typing import List, Optional

from pydantic import BaseModel

from fideslang.models.fides_model import FidesModel


class Organization(FidesModel):
    name: str
    description: str
