from typing import Optional

from fidesctl.lang.models.fides_model import FidesModel


class Registry(FidesModel):
    id: Optional[int]
    organizationId: int
    fidesKey: str
    name: str
    description: str
