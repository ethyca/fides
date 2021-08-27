from typing import Optional

from fideslang.models.fides_model import FidesModel


class Registry(FidesModel):
    organizationId: int
    name: str
    description: str
