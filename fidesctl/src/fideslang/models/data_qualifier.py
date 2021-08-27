from typing import Optional

from fideslang.models.fides_model import FidesModel


class DataQualifier(FidesModel):
    organizationId: int = 1
    name: str
    description: str
